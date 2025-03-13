import os
from dataclasses import dataclass, field, fields
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from typing_extensions import Annotated
from dataclasses import dataclass

DEFAULT_REPORT_STRUCTURE = """Use this structure to create a Geopolitical Risk and Opportunity Report on the user-provided topic:

1. Introduction (no research needed)
   - Brief overview of the topic area

2. Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   
3. Conclusion
   - Aim for 1 structural element (either a list of table) that distills the main body sections 
   - Provide a concise summary of the report"""

# # 1. **Introduction** (No research needed)
#    - Brief overview of the topic area.

# 2. **Historical Context & Current Developments**
#    - Very briefly (1-2 sentences) outline the historical background.
#    - Emphasize how events developed or progressed over recent period.
#    - Focus on **current geopolitical events, policy shifts, and economic impacts** related to the topic.
      
# 3. **Current Impact**
#    - Assess how the topic is **currently influencing global affairs**.
#    - Address **economic, political, security, and societal dimensions**.
#    - Include **major affected entities** (countries, corporations, institutions).

# 4. **Conclusion**
#    - Summarize the report's key insights.
#    - Provide a **structural element** (table or list) to distill the main takeaways.

# DEFAULT_SCENARIO_STRUCTURE = """The Geopolitical Risk and Opportunity Report should explore the most likely scenarios that can emerge regarding the user-provided topic. You should generate **{number_of_queries}** high-probability geopolitical risk & opportunity scenarios.

# Each scenario must follow this structure:

# 1. **Scenario Title:**  
#    - A concise, impactful title summarizing the geopolitical event (e.g., “VGEO Scenario #X: [Title]”).

# 2. **Overview:**  
#    - Provide context and background on the geopolitical landscape.  
#    - Describe key developments—such as elections, policy shifts, or external pressures—that set the stage for the scenario.

# 3. **Scenario Trigger Event:**  
#    - Identify the event that initiates the scenario (e.g., a policy action, trade restriction, security escalation, technological breakthrough, or diplomatic shift).  
#    - Specify the country, institution, or actor responsible, and detail the trigger mechanism.

# 4. **Key Actors & Their Roles:**  
#    - Identify major stakeholders (governments, political parties, multinational corporations, financial institutions, regulatory bodies, etc.).  
#    - Categorize entities as **Initiators, Affected Parties, and Responding Actors**.  
#    - Outline each actor's role, policy agenda, and strategic priorities, including any involvement of alliances, trade blocs, or economic coalitions.

# 5. **Risk & Opportunity Analysis:**  
#    - Break down the scenario's impact into:
#      - **First-Order Effects:** Immediate political, economic, or security impacts.
#      - **Second-Order Effects:** Short-term consequences such as shifts in market sentiment, investor confidence, or diplomatic alignments.
#      - **Third-Order Effects:** Long-term structural changes in global trade, security alliances, energy markets, and financial stability.
#    - Support assessments with historical precedents, policy trends, government statements, corporate reports, and economic data.

# 6. **Conclusion & Strategic Outlook:**  
#    - Summarize key risks and opportunities in a clear table or bullet format.  
#    - Provide actionable insights and recommendations for stakeholders to navigate the evolving geopolitical landscape.

# Ensure that all scenarios are:
# - **Plausible, intelligence-backed, and grounded in current geopolitical developments.**
# - **Clearly structured and distinct from one another, covering a range of potential outcomes.**
# """


@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the chatbot."""
    report_structure: str = DEFAULT_REPORT_STRUCTURE
   #  scenario_structure: str = DEFAULT_SCENARIO_STRUCTURE
    number_of_queries: int = 1 
   #  number_of_scenarios: int =3
    tavily_topic: str = "news" # general
    tavily_days: str = 7
    planner_model: str = "gpt-4o"
    scenario_model: str = "gpt-4o"
    writer_model: str = "gpt-4o-mini"


    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})