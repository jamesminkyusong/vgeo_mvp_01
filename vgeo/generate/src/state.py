from typing import Annotated, List, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
import operator


class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )
    research: bool = Field(
        description="Whether to perform web research for this section of the report."
    )
    content: str = Field(
        description="The content of the section."
    )   

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

class ReportStateInput(TypedDict):
    topic: str # Report topic
    feedback_on_report_plan: str # Feedback on the report structure from review
    accept_report_plan: bool  # Whether to accept or reject the report plan
    
class ReportStateOutput(TypedDict):
    final_report: str # Final report

class ReportState(TypedDict):
    topic: str
    feedback_on_report_plan: str
    accept_report_plan: bool
    sections: list[Section]
    completed_sections: Annotated[list, operator.add]
    report_sections_from_research: str
    final_report: str
    retrieved_documents: list[dict]  # Stores all retrieved full documents
    retrieved_context: str  # Stores formatted text from documents (for easy LLM use)

class SectionState(TypedDict):
    section: Section # Report section   
    search_queries: list[SearchQuery] # List of search queries
    source_str: str # String of formatted source content from web search
    report_sections_from_research: str # String of any completed sections from research to write final sections
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API

class SectionOutputState(TypedDict):
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API
