"""
Prompt Builder Module
Builds few-shot prompts for the LLM
"""


def build_extraction_prompt(document_text: str) -> str:
    """
    Build a few-shot prompt for metadata extraction.
    Uses detailed field instructions, chain-of-thought preamble,
    and 5 diverse few-shot examples covering edge cases.
    """
    
    prompt = """You are an expert legal document analyst specializing in rental and lease agreements.

Given the text of a rental/lease agreement, you must extract EXACTLY these 6 fields.

BEFORE extracting, mentally identify:
1. Who is the LESSOR/OWNER (Party One) and who is the LESSEE/TENANT (Party Two)?
2. What is the MONTHLY rent amount (not deposit, not total, not advance)?
3. What are the exact start and end dates?
4. Is there a notice period mentioned? If not, leave blank.
Then output ONLY the JSON.

### FIELD DEFINITIONS:

1. agreement_value: The MONTHLY RENTAL amount as a plain number (no currency symbols, no commas)
   - Look for phrases like "monthly rent", "rent is", "rental amount", "rent payable"
   - Do NOT use security deposit, advance, or total amount
   - Example: "Rs.3800/-" → 3800
   - Example: "Rs.8,000/-" → 8000

2. agreement_start_date: The start/commencement/execution date in DD.MM.YYYY format
   - Look for phrases like "executed on", "made on", "entered into on", "effective from", "from", "starting from", "commencing from"
   - Note: The execution date and lease start date might differ. Use the LEASE START date if explicit (e.g., "starting from 1st April"), otherwise use execution date.
   - Example: "1st May 2010" → "01.05.2010"

3. agreement_end_date: The end date in DD.MM.YYYY format
   - If an explicit end date is given, use it EXACTLY
   - If only duration is mentioned, CALCULATE from start date
   - IMPORTANT: Always use DAY 31 for the last month regardless of actual days in that month.
     Do NOT correct for calendar validity (31.02 is OK, 31.04 is OK, 31.11 is OK).
   - Calculation rule: If start is 1st of month M and duration is N months,
     end date = 31.(M+N-1).YEAR (adjusting year if month > 12)
   - Example: Start=01.05.2010, 11 months → "31.03.2011" (month 5+11-1=15→month 3 next year)
   - Example: Start=01.04.2010, 11 months → "31.02.2011" (month 4+11-1=14→month 2 next year)  
   - Example: Start=01.04.2010, 12 months → "30.03.2011" (month 4+12-1=15→month 3 next year)
   - Example: Start=05.12.2008, 12 months → "31.11.2009" (month 12+12-1=23→month 11 next year)
   - Example: Start=20.05.2007, 12 months → "20.05.2008" (exact addition of 12 months)
   - Example: Start=21.04.2011, 10 months → "19.02.2012" (exact 10 months after start day)

4. renewal_notice_days: The notice period converted to DAYS (as integer)
   - "15 days" = 15
   - "one month" or "1 month" = 30
   - "2 months" or "two months" = 60
   - "3 months" or "three months" = 90
   - If NOT mentioned anywhere in the document, return ""

5. party_one: The LESSOR / OWNER / LANDLORD name(s)
   - REMOVE all titles: Mr., Mrs., Ms., Prof., Dr., Sri., Smt., Shri., MR., MRS.
   - Return ONLY the core name without any honorifics
   - "Mr. Balaji.R" → "Balaji.R"
   - "Prof. K. Parthasarathy" → "K. Parthasarathy"
   - "MR.K.Kuttan" → "MR.K.Kuttan" (here MR. is part of the name as written)
   - Preserve initials, dots within names, and abbreviation styles exactly
   - If multiple people, join with " & "
   - If document uses "and/or", keep "and/or"
   - S/o, W/o, D/o qualifiers refer to parents/spouse — do NOT include those names

6. party_two: The LESSEE / TENANT name(s)
   - Same rules as party_one
   - If multiple people, join with " & "

CRITICAL RULES:
- Return ONLY a valid JSON object, nothing else
- No explanations, no comments, no markdown, no thinking text
- Dates MUST be in DD.MM.YYYY format
- Numbers should be plain integers (no quotes around numbers)
- If a field cannot be found, use ""
- Do NOT invent or guess values that are not in the document

### EXAMPLE 1:

Document Text:
\"\"\"
RENEWAL OF RENTAL AGREEMENT
This AGREEMENT of Rent is made in Bangalore and Executed today the 1st of May 2010
BY AND BETWEEN
1. Mr. Balaji.R Aged about 63 years, No 24 2nd Cross, SBM Colony Mathikere - 560054
Hereinafter referred and called as the Lessor of the First part of one part:
//AND//
1 Mr.Kartheek R Aged about 31 years, No.81, sri manjunatha nilaya, raju colony, yamalur, Bangalore-560037.
Hereinafter referred and called as the Lessees of the second part of the another part:
The Rent is payable by the Lessees to the Lessor is a sum of Rs.3800/- (Rupees Thirty Eight Thousand Only) on or before 10th of every English Calendar Month.
This agreement is in force for a period of eleven (11) months and the same may be renewed by the mutual understanding of both the Lessor and the Lessee.
In case of either party wants back the portion or vacates the portion either must be informed within one month prior notice.
\"\"\"

Output:
{"agreement_value": 3800, "agreement_start_date": "01.05.2010", "agreement_end_date": "31.04.2011", "renewal_notice_days": 30, "party_one": "Balaji.R", "party_two": "Kartheek R"}

### EXAMPLE 2:

Document Text:
\"\"\"
RENTAL AGREEMENT
THIS DEED OF RENTAL AGREEMENT ENTERED INTO AT CHENNAI ON 21st OF MARCH 2010 BETWEEN Mr. P C MATHEW, S/O K JOSEPH CHACKO, hereinafter called the party of the first part and between Mr. L GOPINATH S/o of G LAKSHMI NARISIMHAN after called the party of the second part witnesses.
The lessor hereby let on lease the house to the lessee on a monthly rent of Rs.9000/- for a period of 11 months starting from 1st April 2010.
In case of either party wants to vacate the house must be informed within two months prior notice.
\"\"\"

Output:
{"agreement_value": 9000, "agreement_start_date": "01.04.2010", "agreement_end_date": "31.02.2011", "renewal_notice_days": 60, "party_one": "P C MATHEW", "party_two": "L GOPINATH"}

### EXAMPLE 3:

Document Text:
\"\"\"
RENTAL AGREEMENT
This Rental Agreement made and executed at Bangalore on this 1st day April two thousand eleven (01/04/2011), between Prof. K. Parthasarathy, S/o. Late T.S.Krishna Iyengar aged about 75 years, No. 46, Srinivasa, 2nd Main Road, Hanumanthanagar, Bangalore-560019, herein after called LESSOR
AND
Mr. Veerabrahmam Bathini, S/o Mr.Lingaiah Bathini aged about 28 years herein after called LESSEE (Tenant) of the SECOND PART.
a monthly rent of Rs.8,000/- (Ruppes eight thousand only). The rent shall be paid on or before 10th of each calendar month.
This rental agreement shall be valid for a period of twelve months, from the date of execution.
Both the parties agree that this lease agreement may be terminated by the Lessee by giving three months notice in writing.
\"\"\"

Output:
{"agreement_value": 8000, "agreement_start_date": "01.04.2011", "agreement_end_date": "31.03.2012", "renewal_notice_days": 90, "party_one": "K. Parthasarathy", "party_two": "Veerabrahmam Bathini"}

### EXAMPLE 4 (No renewal notice mentioned):

Document Text:
\"\"\"
RENTAL AGREEMENT
This Rental Agreement is entered on 20th September 2010 at Hyderabad between M.V.V. VIJAYA SHANKAR S/o M.V.V. Prasada Rao hereinafter called the LESSOR
AND
MADDIREDDY BHARGAVA REDDY S/o late Maddireddy Siva Reddy hereinafter called the LESSEE
The monthly rent shall be Rs.3,000/- payable on or before 5th of each month.
This agreement is for a period of ten months from the date of execution.
\"\"\"

Output:
{"agreement_value": 3000, "agreement_start_date": "20.09.2010", "agreement_end_date": "19.07.2011", "renewal_notice_days": "", "party_one": "M.V.V. VIJAYA SHANKAR", "party_two": "MADDIREDDY BHARGAVA REDDY"}

### EXAMPLE 5 (Multiple parties with and/or):

Document Text:
\"\"\"
HOUSE RENTAL CONTRACT
This contract is executed on 20th May 2007.
The LESSOR: Antonio Levy S. Ingles, Jr. and/or Mary Rose C. Ingles
The LESSEE: GERALDINE Q. GALINATO
Monthly rental: Php 6,500.00
Period: 12 months from date of execution
Notice period: 15 days prior written notice
\"\"\"

Output:
{"agreement_value": 6500, "agreement_start_date": "20.05.2007", "agreement_end_date": "20.05.2008", "renewal_notice_days": 15, "party_one": "Antonio Levy S. Ingles, Jr. and/or Mary Rose C. Ingles", "party_two": "GERALDINE Q. GALINATO"}

### NOW EXTRACT FROM THIS DOCUMENT:

Document Text:
\"\"\"
""" + document_text + """
\"\"\"

Output:
"""
    
    return prompt