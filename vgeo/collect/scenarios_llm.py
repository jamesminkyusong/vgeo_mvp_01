import os
import time
import json
import pandas as pd

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dataclasses import dataclass, field
from typing import List



# Define the structured output schema using a dataclass
@dataclass
class Scenario:
    scenario_summary_title: str
    description: str
    actors: List[str]
    trigger_events: List[str]


@dataclass
class ClusteringConfig:
    cluster_ID: int
    description: str

@dataclass
class ClustersContext:
    cluster_context: List[ClusteringConfig]


# Define the structured output schema using a dataclass
@dataclass
class ClusteredScenario:
    scenario_summary_title: str
    description: str
    actors: List[str]
    trigger_events: List[str]
    Article_ID: str
    cluster_ID: int

############################################################

scenario_extraction_instructions = """
You are an expert in geopolitical analysis. Given the following specific sections of an article that mention geopolitical scenarios, distill into **Standardized Scenarios**.
For ALL **Standardized Scenarios** include:
- "scenario_summary_title": A concise title summarizing the scenario.
- "description": A detailed explanation including context, conditions, or potential outcomes.
- "actors": A list of key actors regarding the current scenario.
- "trigger events": A list of key trigger events that set the current scenario into motion

Return your output as a JSON list of objects matching the Scenario schema.

Text:
{text}
"""

############################################################

scenario_cluster_context_instructions = """
You are a senior geopolitical analyst and clustering expert.
    
Analyze the following list of scenario objects. Each scenario includes:
  - "scenario_summary_title": a concise title.
  - "actors": key actors (such as politicians, corporates, countries).
  - "trigger_events": events that set the scenario in motion.

Your task is to generate between three and eight distinct clusters that capture the nuanced geopolitical narratives 
and industry-focused themes present across these scenarios.

Each cluster should be represented as an object with:
  - "cluster_ID": an integer starting at 0.
  - "cluster_description": a brief geopolitical narrative description of that cluster.

Return your output as a JSON object with a single key **cluster_context** containing an array of cluster objects 
matching the following schema:
  "cluster_ID": str, "cluster_description": str

Here are the scenarios:
{scenarios}
"""

############################################################

scenario_cluster_instructions = """
You are an senior geopolitical analyst. Given the following specific list of **Scenarios**, cluster these into similar groupings based on the provided **Grouping Guideline**.

You SHOULD NOT edit any of the features below for the **CURRENT SCENARIO**:
- "scenario_summary_title": A concise title summarizing the scenario.
- "description": A detailed explanation including context, conditions, or potential outcomes.
- "actors": A list of key actors regarding the current scenario.
- "trigger events": A list of key trigger events that set the current scenario into motion
- "Article_ID": Identifer for another database

You SHOULD ONLY add the **cluster_ID** infromation and return your output as a JSON objects matching the ClusteredScenario schema.

**Grouping Guideline**:
{grouping_guideline}

CURRENT SCENARIO TO ADD **cluster_ID**:
{curr}

"""
############################################################

def load_kws():
    with open('vgeo/collect/kw_phrases.txt', 'r') as f:
        kws = f.read()
    kw_list = kws.split("</kw>")
    return kw_list

def scenario_boolean(df):
    kw_list = load_kws()
    sc_bools = []
    for c in df['cleaned_content']:
        found_bool = False
        for kw in kw_list:
            if kw in c:
                found_bool = True
        sc_bools.append(found_bool)
    df['scenario_boolean'] = sc_bools
    return df

def only_scenarios_df(df):
    curr_df = df[df['scenario_boolean']]
    curr_df.reset_index(inplace=True)
    return curr_df

def initial_scenario_json_generate(df):
    ct = df['cleaned_content'].tolist()
    aid = df['Article_ID'].tolist()
    resps = []
    for n, c in enumerate(ct):
        try:
            prompt = scenario_extraction_instructions.format(text=c)

            llm = ChatOpenAI(model= "gpt-4o", temperature=0)
            structured_llm = llm.with_structured_output(Scenario)
            sc_response = structured_llm.invoke([HumanMessage(content=prompt)])
            sc_response['Article_ID'] = aid[n]
            # Print the structured JSON output
            resps.append(sc_response)
            time.sleep(0.2)
        except:
            empty_scenario = {
                "scenario_summary_title": "",
                "description": "",
                "actors": [],
                "trigger_events": [],
                "Article_ID": aid[n]
            }
            resps.append(empty_scenario)

    return resps


def generate_clusters_context(scenarios: List[dict]):
    scenarios = [
        {key: value for key, value in item.items() if key != "description" and key != "Article_ID"} 
        for item in scenarios
    ]  
    scenario_json_str = json.dumps(scenarios, indent=2)
    try:
        # llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b")
        llm = ChatOpenAI(model="gpt-4o")
        prompt = scenario_cluster_context_instructions.format(scenarios= scenario_json_str)
        structured_llm = llm.with_structured_output(ClustersContext)
        
        # Invoke the LLM with our prompt
        response = structured_llm.invoke([HumanMessage(content=prompt)])
    
    # simple task so should run again..
    except:
        # llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b")
        llm = ChatOpenAI(model="gpt-4o")
        prompt = scenario_cluster_context_instructions.format(scenarios= scenario_json_str)
        structured_llm = llm.with_structured_output(ClustersContext)
        
        # Invoke the LLM with our prompt
        response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response

def scenario_clustering(scenarios, grouping_guideline):
    final_response = []
    for n, r in enumerate(scenarios):
        r_str = json.dumps(r, indent=2)

        prompt = scenario_cluster_instructions.format(grouping_guideline= grouping_guideline, curr= r_str )

        llm = ChatOpenAI(model= "gpt-4o", temperature=0)

        structured_llm = llm.with_structured_output(ClusteredScenario)
        c_response = structured_llm.invoke([HumanMessage(content=prompt)])

        final_response.append(c_response )

    return final_response

