## 1. Sample Queries
(France OR Macron OR Germany OR Merz) AND (nuclear OR "nuclear umbrella") AND (Trump OR Russia OR USA OR "United States of America")

trump AND (tariff OR trade) AND ("international relations" OR "diplomatic tensions" OR trade) AND (Colombia OR Canada OR China OR EU OR Japan OR Mexico)

ukraine AND (russia OR moscow) AND (Zlelensky OR Zelenskyy OR Putin OR Trump) AND (ceasefire OR "peace talks" OR invasion)

## 2. GDELT Query Formatting Rules

GDELT accepts queries in a specific format. Follow these guidelines to ensure your queries are valid:

### **Overall Structure:**  
   - Queries must be composed of two groups connected by an `AND` operator.  
   - Each group is enclosed in parentheses and contains terms combined using the `OR` operator.
   - **Valid Example:**  
     ```
     (A OR B) AND (C OR "D E")
     ```

### **Double Quotes Usage:**  
   - **Only use double quotes for multi-word phrases.**  
   - Single words should **not** be enclosed in double quotes.  
   - **Invalid Example:**  
     ```
     ("A" OR "B") AND (C OR "D E")
     ```  
     Here, "A" and "B" are single words and should be unquoted (i.e. `A OR B`).

### **Operator Restrictions Within Parentheses:**  
   - **Only the `OR` operator is allowed inside parentheses.**  
   - Do not include the `AND` operator within any set of parentheses.
   - For example, the following is **not allowed**:  
     ```
     (A AND B) AND (C OR "D E")
     ```

## 3. Languages (only major languages listed; max 7 at once)
- English (eng), 
- Spanish (spa), 
- Chinese (zho), 
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
