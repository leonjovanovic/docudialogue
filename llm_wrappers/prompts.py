ENTITY_TYPE_GENERATION_PROMPT = """
The goal is to study the connections and relations between the entity types and their features in order to understand all available information from the text.
As part of the analysis, you want to identify the entity types present in the following text.
Avoid general entity types such as "other" or "unknown".
Follow these steps:
Step 1: Extract all types of present entities in text. Each entity type should represent certain group of entities. Don't worry about quantity, always choose quality over quantity. Types can be specific but not too specific and they should be relevant to the text subject.
Step 2: Double check types you found and remove redundant or overlapping ones and keep only one. For example, if, in step 1, you found "company" and "organization" entity types, you should keep only one of them.
=====================================================================
EXAMPLE SECTION: The following section includes example output. These examples **must be excluded from your answer**.

EXAMPLE
Text: Industry leaders such as Panasonic are vying for supremacy in the battery production sector. They are investing heavily in research and development and are exploring new technologies to gain a competitive edge.
RESPONSE:
organization, technology, sectors, investment strategies
END OF EXAMPLE
======================================================================

======================================================================
REAL DATA: The following section is the real data. You should use only this real data to prepare your answer. Generate Entity Types only.
Text: {input_text}
RESPONSE:
{{<entity_types>}}
"""

ENTITY_GENERATION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text.

Identify all entities. For each identified entity, extract the following information:
- name: Name of the entity, capitalized
- type: One of the following types: [{entity_types}]
- description: Comprehensive description of the entity's attributes and activities


######################
-Examples-
######################
Example 1:
Entity_types: ORGANIZATION,PERSON
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
[
  {{"name": "CENTRAL INSTITUTION", "type": "ORGANIZATION", "description": "The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday"}},
  {{"name": "MARTIN SMITH", "type": "PERSON", "description": "Martin Smith is the chair of the Central Institution"}},
  {{"name": "MARKET STRATEGY COMMITTEE", "type": "ORGANIZATION", "description": "The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply"}},
]

######################
Example 2:
Entity_types: ORGANIZATION
Text:
TechGlobal's (TG) stock skyrocketed in its opening day on the Global Exchange Thursday. But IPO experts warn that the semiconductor corporation's debut on the public markets isn't indicative of how other newly listed companies may perform.

TechGlobal, a formerly public company, was taken private by Vision Holdings in 2014. The well-established chip designer says it powers 85% of premium smartphones.
######################
Output:
[
  {{"name": "TECHGLOBAL", "type": "ORGANIZATION", "description": "TechGlobal is a stock now listed on the Global Exchange which powers 85% of premium smartphones"}},
  {{"name": "VISION HOLDINGS", "type": "ORGANIZATION", "description": "Vision Holdings is a firm that previously owned TechGlobal"}},
]

######################

-Real Data-
######################
entity_types: {entity_types}
text: {input_text}
######################
output:
"""

RELATIONSHIPS_GENERATION_PROMPT = """
-Goal-
Given a text document and a list of entities, identify all relationships among the provided entities.

From the provided entities, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name and type of the source entity, as provided
- target_entity: name and type of the target entity, as provided
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity

######################
-Examples-
######################
Example 1:
Entities: {{"name": "CENTRAL INSTITUTION", type: "ORGANIZATION", "name": "MARTIN SMITH", type: "PERSON", "name": "MARKET STRATEGY COMMITTEE", type: "ORGANIZATION"}}
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
[
    {{"subject": ["MARTIN SMITH", "PERSON"], "object": ["CENTRAL INSTITUTION", "ORGANIZATION"], "relationship_description": "Martin Smith is the Chair of the Central Institution and will answer questions at a press conference", "relationship_strength": 9}}
]
VERY IMPORTANT: Make sure entity name and type are identical one from provided entites. They will be used for identification later.

######################
-Real Data-
######################
entities: {entities}
text: {input_text}
######################
output:
"""

ENTITY_RELATIONSHIPS_GENERATION_PROMPT = """
-Goal-
Given a text document and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: an integer score between 1 to 10, indicating strength of the relationship between the source entity and target entity


######################
-Examples-
######################
Example 1:
Entity_types: ORGANIZATION,PERSON
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
######################
Output:
{{
  "entities": [
    {{"name": "CENTRAL INSTITUTION", "type": "ORGANIZATION", "description": "The Central Institution is the Federal Reserve of Verdantis, which is setting interest rates on Monday and Thursday"}},
    {{"name": "MARTIN SMITH", "type": "PERSON", "description": "Martin Smith is the chair of the Central Institution"}},
    {{"name": "MARKET STRATEGY COMMITTEE", "type": "ORGANIZATION", "description": "The Central Institution committee makes key decisions about interest rates and the growth of Verdantis's money supply"}},
  ],
  "relationships": [
      {{"subject": ["MARTIN SMITH", "PERSON"], "object": ["CENTRAL INSTITUTION", "ORGANIZATION"], "relationship_description": "Martin Smith is the Chair of the Central Institution and will answer questions at a press conference", "relationship_strength": 9}}
  ]
}}

######################
Example 2:
Entity_types: ORGANIZATION,GEO,PERSON
Text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.
######################
Output:
{{
  "entities": [
    {{"name": "FIRUZABAD", "type": "GEO", "description": "Firuzabad held Aurelians as hostages"}},
    {{"name": "AURELIA", "type": "GEO", "description": "Country seeking to release hostages"}},
    {{"name": "QUINTARA", "type": "GEO", "description": "Country that negotiated a swap of money in exchange for hostages"}},
    {{"name": "TIRUZIA", "type": "GEO", "description": "Capital of Firuzabad where the Aurelians were being held"}},
    {{"name": "KROHAARA", "type": "GEO", "description": "Capital city in Quintara"}},
    {{"name": "CASHION", "type": "GEO", "description": "Capital city in Aurelia"}},
    {{"name": "SAMUEL NAMARA", "type": "PERSON", "description": "Aurelian who spent time in Tiruzia's Alhamia Prison"}},
    {{"name": "ALHAMIA PRISON", "type": "GEO", "description": "Prison in Tiruzia"}},
    {{"name": "DURKE BATAGLANI", "type": "PERSON", "description": "Aurelian journalist who was held hostage"}},
    {{"name": "MEGGIE TAZBAH", "type": "PERSON", "description": "Bratinas national and environmentalist who was held hostage"}},
  ],
  "relationships": [
      {{"subject": ["FIRUZABAD", "GEO"], "object": ["AURELIA", "GEO"], "relationship_description": "Firuzabad negotiated a hostage exchange with Aurelia", "relationship_strength": 2}}
      {{"subject": ["QUINTARA", "GEO"], "object": ["AURELIA", "GEO"], "relationship_description": "Quintara brokered the hostage exchange between Firuzabad and Aurelia", "relationship_strength": 2}}
      {{"subject": ["QUINTARA", "GEO"], "object": ["FIRUZABAD", "GEO"], "relationship_description": "Quintara brokered the hostage exchange between Firuzabad and Aurelia", "relationship_strength": 2}}
      {{"subject": ["SAMUEL NAMARA", "PERSON"], "object": ["ALHAMIA PRISON", "GEO"], "relationship_description": "Samuel Namara was a prisoner at Alhamia prison", "relationship_strength": 8}}
      {{"subject": ["SAMUEL NAMARA", "PERSON"], "object": ["MEGGIE TAZBAH", "PERSON"], "relationship_description": "Samuel Namara and Meggie Tazbah were exchanged in the same hostage release", "relationship_strength": 2}}
      {{"subject": ["SAMUEL NAMARA", "PERSON"], "object": ["DURKE BATAGLANI", "PERSON"], "relationship_description": "Samuel Namara and Durke Bataglani were exchanged in the same hostage release", "relationship_strength": 2}}
      {{"subject": ["MEGGIE TAZBAH", "PERSON"], "object": ["DURKE BATAGLANI", "PERSON"], "relationship_description": "Meggie Tazbah and Durke Bataglani were exchanged in the same hostage release", "relationship_strength": 2}}
      {{"subject": ["SAMUEL NAMARA", "PERSON"], "object": ["FIRUZABAD", "GEO"], "relationship_description": "Samuel Namara was a hostage in Firuzabad", "relationship_strength": 2}}
      {{"subject": ["MEGGIE TAZBAH", "PERSON"], "object": ["FIRUZABAD", "GEO"], "relationship_description": "Meggie Tazbah was a hostage in Firuzabad", "relationship_strength": 2}}
      {{"subject": ["DURKE BATAGLANI", "PERSON"], "object": ["FIRUZABAD", "GEO"], "relationship_description": "Durke Bataglani was a hostage in Firuzabad", "relationship_strength": 2}}
  ]
}}

-Real Data-
######################
entity_types: {entity_types}
text: {input_text}
######################
output:
"""

SUMMARIZE_DESCRIPTIONS_PROMPT = """
You will be given list of descriptions that describe certain entity or relationship. Your job is to provide short summary that captures all of the distinct information from each description. Purpose of summarization is for each entity or relationship to have a single concise description.

Here are the descriptions: {descriptions}
"""