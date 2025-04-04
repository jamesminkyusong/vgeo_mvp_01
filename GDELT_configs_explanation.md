
## 1. Sample Queries
(France OR Macron OR Germany OR Merz) AND (nuclear OR "nuclear umbrella") AND (Trump OR Russia OR USA OR "United States of America")

trump AND (tariff OR trade OR "trade deficit" OR"international relations" OR "diplomatic tensions") AND ("dirty 15" OR Colombia OR India OR Canada OR China OR EU OR Japan OR Mexico OR "South Korea")

ukraine AND (russia OR moscow OR "Saudi Arabia") AND (Zlelensky OR Zelenskyy OR Putin OR Trump) AND (ceasefire OR "peace talks" OR invasion)

("European Union" OR EU) AND ("precious minerals" OR "critical minerals" OR "strategic minerals" OR gallium) AND (production OR supply OR demand OR dependecy OR dependant) AND (Greece OR China)

(Russia OR Putin) AND (Arctic OR Svalbard) AND (Norway OR "Norwegian territory") AND ("military presence" OR "territorial claims" OR conflict OR tensions)

## 2. GDELT Query Formatting Rules

GDELT queries are built by combining **groups** of alternative search terms. The goal is to ensure that your query clearly specifies alternatives (using OR) and combines independent conditions (using AND) without mixing these operators improperly.

### **Overall Structure:**
- **Group Alternatives with OR:**  
  **ENCLOSE** a set of related or alternative terms within parentheses, **grouping** them with the **OR** operator.  
  *Example:*  
  ```
  (France OR Macron OR Germany)
  ```
- **Combine Groups with AND:**  
  When you need to require that multiple independent conditions are met, join these **groups** with the **AND** operator. Note that **AND should only be used between parentheses**, not inside them.  
  *Example:*  
  ```
  (France OR Macron OR Germany) AND (nuclear OR "nuclear umbrella")
  ```
- **Flexibility in Structure:**  
  While many queries are formed by combining two groups, a query can consist of one or more groups. The key is that within each group, only OR is allowed.

### **General Guideline:**
- **Enclose Alternatives with Parentheses:**  
  Always put multiple alternative terms **within parentheses** and separate them with **OR**.
- **AND Only Outside:**  
  Use the AND operator only to connect distinct groups of alternatives (parentheses); **do not use it inside any parentheses**.
- **Double Quotes for Phrases:**  
  Only wrap multi-word phrases in double quotes. Do not use quotes for single words.
- **Keep It Clear:**  
  Think of each parenthetical group as a “bucket” of alternatives. The query will only match records if every “bucket” (each connected by AND) has at least one matching term.

### **Double Quotes Usage:**
- **Correct Usage:**  
  Use double quotes to enclose multi-word phrases, e.g., `"nuclear umbrella"`.
- **Incorrect Usage:**  
  Do not enclose single words in double quotes.  
  *Invalid Example:*  
  ```
  ("France" OR "Macron") AND (nuclear OR "nuclear umbrella")
  ```
  Here, "France" and "Macron" should not be quoted because they are single words.

### **Operator Restrictions Within Parentheses:**
- **Only OR Allowed:**  
  Inside any set of parentheses, you should only use the OR operator.  
- **Avoid Mixing Operators:**  
  Do not include the AND operator inside parentheses.  
  *Invalid Example:*  
  ```
  (France AND Macron) AND (nuclear OR "nuclear umbrella")
  ```
## 3. Languages (only major languages listed; max 7 at once)
- English (eng), 
- Spanish (spa), 
- Chinese (zho), GDELT does not distinguish between mandarin, cantonese, etc 
- German (deu),
- French (fra),
- Korean (kor),
- Ukranian (ukr),
- Russian (rus)

## 4. Countries (only major countries listed; max 7 at once)
- USA (US)
- Germany (GM)
- France (FR)
- Russia (RS)
- Ukraine (UP)
- Mexico (MX)
- Colombia (CO)
- Canada (CA)
- South Korea (KS)
- Taiwan (TW)
- Hong Kong (HK)
- China (CH)

