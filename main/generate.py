import os
import sys
import asyncio
import configparser
from datetime import datetime

from dataclasses import dataclass, field
from typing import List, Tuple
import pandas as pd
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

def load_configs():
    config = configparser.ConfigParser()
    config.read('main/generate_settings.ini')

    os.environ['TAVILY_API_KEY']= config['API_KEYS']['TAVILY_KEY'].strip()
    os.environ['OPENAI_API_KEY']= config['API_KEYS']['OPENAI_API_KEY'].strip()
    os.environ['GOOGLE_API_KEY']= config['API_KEYS']['GOOGLE_API_KEY'].strip()

    os.environ['ZILLIZ_CLOUD_URI']= config['API_KEYS']['ZILLIZ_CLOUD_URI'].strip()
    os.environ['ZILLIZ_CLOUD_USERNAME']= config['API_KEYS']['ZILLIZ_CLOUD_USERNAME'].strip()
    os.environ['ZILLIZ_CLOUD_PASSWORD']= config['API_KEYS']['ZILLIZ_CLOUD_PASSWORD'].strip()
    os.environ['ZILLIZ_CLOUD_API_KEY']= config['API_KEYS']['ZILLIZ_CLOUD_API_KEY'].strip()
    user_topic = config['GENERATE_INPUT']['TOPIC'].strip()
    output_path = config['GENERATE_CUSTOM_CONFIG']['EXPORT_PATH'].strip()
    selected_scenarios_path = config['GENERATE_CUSTOM_CONFIG']['CUSTOM_SELECTED_SCENARIO_PATH'].strip()

    return user_topic, output_path, selected_scenarios_path

user_topic, output_path, selected_scenarios_path = load_configs()    

# Import Tavily utilities from your existing utils.py file
from vgeo.generate.src.utils import (
    tavily_search_async, 
    deduplicate_and_format_sources, 
    deduplicate_and_format_milvus_sources,
    format_selected_scenarios,
    format_cluster_info
)

from vgeo.generate.src.prompts import (
    query_writer_instructions,
    hc_rd_writer_instructions,
    ci_writer_instructions,
    intro_section_writer_instructions,
    concl_section_writer_instructions,
    scenario_title_generation_instructions,
    scenario_section_instruction_1,
    scenario_section_instruction_2,
)

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Milvus
from pydantic import BaseModel, Field

#  -----------------------
# Configuration and Data Models
# -----------------------


@dataclass
class Config:
    topic: str
    model_name: str = "gpt-4o"        # LLM model name
    tavily_topic: str = "news"        # For Tavily searches (news or general)
    tavily_days: int = 7              # Number of days to look back in retrieval
    number_of_queries: int = 2        # Number of search queries to generate per section
    number_of_scenarios: int = 3

@dataclass
class Paragraph:
    title: str
    content: str = ""


class Scenario(BaseModel):
    title: str = Field(..., description="A scenario section title.")

class Scenarios(BaseModel):
    scenarios: List[Scenario] = Field(..., description="List of generated scenario titles.")

class SearchQuery(BaseModel):
    search_query: str = Field(..., description="Query for web search.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(..., description="List of search queries.")


@dataclass
class Report:
    topic: str
    paragraphs: List[Paragraph] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    scenarios: List[Paragraph] = field(default_factory=list)


    def add_paragraph(self, paragraph: Paragraph):
        self.paragraphs.append(paragraph)

    def add_scenario(self, scenario: Paragraph):
        self.scenarios.append(scenario)

    def add_sources(self, sources: List[str]):
        self.sources.extend(sources)

    def compile(self) -> str:
        report_text = "\n\n".join(f"{p.title}\n{p.content}" for p in self.paragraphs)
        # if self.sources:
        #     works_cited = "Works Cited:\n" + "\n".join(self.sources)
        #     report_text += "\n\n" + works_cited
        if self.scenarios:
            scenarios_text = "\n\n".join(f"{s.title}\n{s.content}" for s in self.scenarios)
            report_text += "\n\n" + scenarios_text
        return report_text


# -----------------------
# Vector Store Functions
# -----------------------

def get_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = Milvus(
        embeddings,
        connection_args={
            "uri": os.getenv("ZILLIZ_CLOUD_URI"),
            "user": os.getenv("ZILLIZ_CLOUD_USERNAME"),
            "password": os.getenv("ZILLIZ_CLOUD_PASSWORD"),
            "secure": True,
        },
        collection_name="LangChainCollection",
    )
    return vector_store

def retrieve_relevant_documents(query, k=2):
    """Retrieves relevant documents from Milvus based on semantic similarity."""
    vector_store = get_vector_store()
    result = vector_store.similarity_search(query, k=k)
    return result

# -----------------------
# Helper Functions
# -----------------------

def generate_paragraph(prompt: str, model: ChatOpenAI) -> str:
    message = HumanMessage(content=prompt)
    response = model.invoke([message])
    return response.content

def generate_search_queries(section_topic: str, main_topic: str, number_of_queries: int, model: ChatOpenAI) -> List[str]:
    prompt = query_writer_instructions.format(
        section_topic=section_topic,
        main_topic=main_topic,
        number_of_queries=number_of_queries
    )
    # Use the model's structured output functionality.
    structured_llm = model.with_structured_output(Queries)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return [q.search_query for q in response.queries]

async def build_section(section_title: str, section_prompt_template: str, config: Config, llm: ChatOpenAI) -> Tuple[str, List[str]]:
    """
    Builds a section by:
    1. Generating dynamic search queries.
    2. Performing asynchronous Tavily searches.
    3. Retrieving relevant documents from a vector store.
    4. Deduplicating and formatting the retrieved sources.
    5. Combining contexts from both sources.
    6. Generating the section content using the combined context.
    
    Returns the section content and a list of source citations.
    """
    # Generate dynamic search queries for this section.
    queries = generate_search_queries(section_title, config.topic, config.number_of_queries, llm)
    
    # --- Tavily Retrieval ---
    try:
        tavily_responses = await tavily_search_async(queries, config.tavily_topic, config.tavily_days)
        retrieved_context_tavily, docs_tavily = deduplicate_and_format_sources(tavily_responses, max_tokens_per_source=1000, include_raw_content=True)
    except Exception as e:
        retrieved_context_tavily = ""
        docs_tavily = []
    
    # --- Vector Store Retrieval ---
    vector_docs = []
    for query in queries:
        results = retrieve_relevant_documents(query, k=2)
        vector_docs.extend(results)
    retrieved_context_vector, docs_vector = deduplicate_and_format_milvus_sources(vector_docs, max_tokens_per_source=1000)
    
    # --- Combine Contexts ---
    combined_context = retrieved_context_tavily + "\n\n" + retrieved_context_vector
    
    # Build the section content by injecting the combined context into the prompt.
    section_prompt = section_prompt_template.format(main_topic=config.topic, section_topic = section_title, context=combined_context)
    section_content = generate_paragraph(section_prompt, llm)
    
    # # Extract citations (if needed, here we could merge citations from both sources)
    # citations_tavily = [doc["citation"] for doc in docs_tavily]
    # citations_vector = [f"{doc['title']} (Vector Search)" for doc in docs_vector]
    # citations = citations_tavily + citations_vector
    
    return section_content

def generate_scenario_titles(report_context: str, cluster_info:str, selected_scenarios: str, main_topic: str, llm: ChatOpenAI) -> List[str]:
    """
    Generates potential scenario titles based on the final report context using structured output.
    """
    prompt = scenario_title_generation_instructions.format(
        main_topic=main_topic,
        general_overview_report=report_context,
        cluster_information= cluster_info,
        relevant_scenarios =selected_scenarios
    )
    # Use structured_llm.invoke for structured output.
    structured_llm = llm.with_structured_output(Scenarios)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    titles = [scenario.title for scenario in response.scenarios]
    return titles

async def generate_scenario_section(scenario_title: str, report_context: str, main_topic: str, llm: ChatOpenAI, config: Config) -> str:
    # Generate scenario-specific search queries using the scenario title.
    scenario_queries = generate_search_queries(scenario_title, main_topic, config.number_of_queries, llm)
    
    # Perform asynchronous Tavily search for scenario queries.
    try:
        tavily_responses = await tavily_search_async(scenario_queries, config.tavily_topic, config.tavily_days)
        scenario_tavily_context, _ = deduplicate_and_format_sources(tavily_responses, max_tokens_per_source=1000, include_raw_content=True)
    except Exception as e:
        print(f"Error during Tavily retrieval for scenario: {e}")
        scenario_tavily_context = ""
    
    # Combine contexts: include the main report context and the scenario-specific Tavily context as separate sections.
    combined_context = f"Main Report Context:\n{report_context}\n\nScenario Tavily Context:\n{scenario_tavily_context}"
    
    # Step 1: Generate the initial part of the scenario section.
    part1_prompt = scenario_section_instruction_1.format(
        scenario_title=scenario_title,
        main_topic=main_topic,
        context=combined_context
    )
    part1 = generate_paragraph(part1_prompt, llm)
    
    # Step 2: Generate the Risk & Opportunity Analysis portion using Part 1 as context.
    part2_prompt = scenario_section_instruction_2.format(
        scenario_title=scenario_title,
        main_topic=main_topic,
        previous_section=part1,  # Pass the previously generated text
        context = combined_context
    )
    part2 = generate_paragraph(part2_prompt, llm)
    
    return part1 + "\n\n" + part2



# -----------------------
# Main Execution Flow (Asynchronous)
# -----------------------

async def generate_report(selected_scenarios_df, cluster_info_df):
    config = Config(topic=user_topic)

    # Initialize LLM model.
    llm = ChatOpenAI(model=config.model_name, temperature=0)
    
    report = Report(topic=config.topic)
    
    # Build Introduction using imported intro prompt.
    intro_content = await build_section("Introduction", intro_section_writer_instructions, config, llm)
    report.add_paragraph(Paragraph(title="", content=intro_content))
    # report.add_sources(intro_sources)
    
    # Build Historical Context & Recent Developments
    hist_content = await build_section("Historical Context & Recent Developments", hc_rd_writer_instructions, config, llm)
    report.add_paragraph(Paragraph(title="", content=hist_content))
    # report.add_sources(hist_sources)
    
    # Build Current Impact and Potential Ramifications
    current_content = await build_section("Current Impact and Potential Ramifications", ci_writer_instructions, config, llm)
    report.add_paragraph(Paragraph(title="", content=current_content))
    # report.add_sources(current_sources)
    
    # Generate Conclusion
    conclusion_prompt = concl_section_writer_instructions.format(main_topic=config.topic, section_topic= "Conclusion", context="")  # if you have additional context, include it here
    conclusion_content = generate_paragraph(conclusion_prompt, llm)
    report.add_paragraph(Paragraph(title="", content=conclusion_content))
    
    main_report_text = report.compile()
    ###### MAIN REPORT COMPLETE ######

    # load selected scenarios 
    if selected_scenarios_path!="":
        try:
            selected_scenarios_df = pd.read_excel(selected_scenarios_path, sheet_name='Selected_Scenarios')
            cluster_info_df = pd.read_excel(selected_scenarios_path, sheet_name='Cluster_Info')
        except:
            pass        
    selected_scenarios_text= format_selected_scenarios(selected_scenarios_df)
    cluster_info_text= format_cluster_info(cluster_info_df)

    # Generate scenario titles using structured_llm.invoke.
    scenario_titles = generate_scenario_titles(
        report_context= main_report_text, 
        cluster_info=cluster_info_text, 
        selected_scenarios= selected_scenarios_text, 
        main_topic= config.topic, 
        llm= llm
    )


    # For each scenario, generate a scenario section and add it to the report.
    for scenario_title in scenario_titles:
        scenario_content = await generate_scenario_section(scenario_title, main_report_text, config.topic, llm, config)
        report.add_scenario(Paragraph(title=f"## {scenario_title}", content=scenario_content))
    
    # Re-compile the report with scenario sections appended.
    final_report = report.compile()
    # print("\n=== Final Report with Scenarios ===")
    # print(final_report)
    return final_report

def main(df1, df2, path):
    report = asyncio.run(generate_report(df1, df2))
    today_string = datetime.today().strftime('%y%m%d%H%M')
    filename = f"{today_string}_final_report.md"
    if path != "":
        output_path = path

    # Write the final report string to the Markdown file.
    with open(os.path.join(output_path, filename), "w", encoding="utf-8") as f:
        f.write(report)
    

if __name__ == "__main__":
    df1 = []
    df2 = []
    main(df1, df2, output_path)