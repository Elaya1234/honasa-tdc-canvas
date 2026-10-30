const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

const samplesDir = path.join(__dirname, 'samples');
if (!fs.existsSync(samplesDir)) {
  fs.mkdirSync(samplesDir, { recursive: true });
}

// 1. The Derma Co 1% Hyaluronic Sunscreen Aqua Gel 30-Day KYC
const tdcData = [
  {
    Customer_ID: "TDC-CUST-1001",
    Customer_Name: "Pooja Sharma",
    Phone_Number: "+91 98201 44521",
    City: "Bengaluru",
    Product_SKU: "TDC-SUN-AQUA-50G",
    Purchase_Date: "2026-10-02",
    Skin_Type: "Oily / Combination",
    "Q1: Daily usage compliance & reapplication frequency?": "",
    "Q2: White cast or skin greasy residue observed?": "",
    "Q3: Pilling under makeup or eye stinging?": "",
    "Q4: Breakouts/irritation or skin sensitivity changes?": "",
    "Q5: Likelihood of repurchase & price satisfaction?": ""
  },
  {
    Customer_ID: "TDC-CUST-1002",
    Customer_Name: "Aditya Verma",
    Phone_Number: "+91 98450 77123",
    City: "Hyderabad",
    Product_SKU: "TDC-SUN-AQUA-50G",
    Purchase_Date: "2026-10-05",
    Skin_Type: "Acne-prone",
    "Q1: Daily usage compliance & reapplication frequency?": "",
    "Q2: White cast or skin greasy residue observed?": "",
    "Q3: Pilling under makeup or eye stinging?": "",
    "Q4: Breakouts/irritation or skin sensitivity changes?": "",
    "Q5: Likelihood of repurchase & price satisfaction?": ""
  },
  {
    Customer_ID: "TDC-CUST-1003",
    Customer_Name: "Neha Kulkarni",
    Phone_Number: "+91 97112 88490",
    City: "Pune",
    Product_SKU: "TDC-SUN-AQUA-80G",
    Purchase_Date: "2026-10-07",
    Skin_Type: "Dry / Normal",
    "Q1: Daily usage compliance & reapplication frequency?": "",
    "Q2: White cast or skin greasy residue observed?": "",
    "Q3: Pilling under makeup or eye stinging?": "",
    "Q4: Breakouts/irritation or skin sensitivity changes?": "",
    "Q5: Likelihood of repurchase & price satisfaction?": ""
  },
  {
    Customer_ID: "TDC-CUST-1004",
    Customer_Name: "Karthik Raja",
    Phone_Number: "+91 99403 11209",
    City: "Chennai",
    Product_SKU: "TDC-SUN-AQUA-50G",
    Purchase_Date: "2026-10-10",
    Skin_Type: "Sensitive",
    "Q1: Daily usage compliance & reapplication frequency?": "",
    "Q2: White cast or skin greasy residue observed?": "",
    "Q3: Pilling under makeup or eye stinging?": "",
    "Q4: Breakouts/irritation or skin sensitivity changes?": "",
    "Q5: Likelihood of repurchase & price satisfaction?": ""
  },
  {
    Customer_ID: "TDC-CUST-1005",
    Customer_Name: "Simran Kaur",
    Phone_Number: "+91 98110 55678",
    City: "Delhi NCR",
    Product_SKU: "TDC-SUN-AQUA-80G",
    Purchase_Date: "2026-10-12",
    Skin_Type: "Combination",
    "Q1: Daily usage compliance & reapplication frequency?": "",
    "Q2: White cast or skin greasy residue observed?": "",
    "Q3: Pilling under makeup or eye stinging?": "",
    "Q4: Breakouts/irritation or skin sensitivity changes?": "",
    "Q5: Likelihood of repurchase & price satisfaction?": ""
  }
];

const wsTdc = XLSX.utils.json_to_sheet(tdcData);
const wbTdc = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wbTdc, wsTdc, "TDC_Sunscreen_KYC");
XLSX.writeFile(wbTdc, path.join(samplesDir, "HONASA_TDC_Sunscreen_30Day_KYC.xlsx"));

// 2. Mamaearth Onion Shampoo Post-Purchase Survey (CSV)
const mamaData = [
  {
    Ticket_ID: "ME-TKT-501",
    Consumer_Name: "Ananya Deshmukh",
    Contact_No: "+91 98234 11098",
    Region: "Mumbai",
    Product_Variant: "Onion Shampoo 400ml",
    Order_Value: "₹499",
    "Q1: Hair fall reduction observed after 3 weeks?": "",
    "Q2: Scalp cleansing & dryness feedback?": "",
    "Q3: Fragrance & lathering experience?": "",
    "Q4: Compared to previously used shampoo?": "",
    "Q5: Net Promoter Score (1-10) & Reason?": ""
  },
  {
    Ticket_ID: "ME-TKT-502",
    Consumer_Name: "Rohan Nair",
    Contact_No: "+91 97455 22345",
    Region: "Kochi",
    Product_Variant: "Onion Shampoo 250ml",
    Order_Value: "₹349",
    "Q1: Hair fall reduction observed after 3 weeks?": "",
    "Q2: Scalp cleansing & dryness feedback?": "",
    "Q3: Fragrance & lathering experience?": "",
    "Q4: Compared to previously used shampoo?": "",
    "Q5: Net Promoter Score (1-10) & Reason?": ""
  },
  {
    Ticket_ID: "ME-TKT-503",
    Consumer_Name: "Meenakshi Sundaram",
    Contact_No: "+91 94441 88765",
    Region: "Madurai",
    Product_Variant: "Onion Shampoo 600ml Pump",
    Order_Value: "₹699",
    "Q1: Hair fall reduction observed after 3 weeks?": "",
    "Q2: Scalp cleansing & dryness feedback?": "",
    "Q3: Fragrance & lathering experience?": "",
    "Q4: Compared to previously used shampoo?": "",
    "Q5: Net Promoter Score (1-10) & Reason?": ""
  }
];

const wsMama = XLSX.utils.json_to_sheet(mamaData);
const csvContent = XLSX.utils.sheet_to_csv(wsMama);
fs.writeFileSync(path.join(samplesDir, "HONASA_Mamaearth_Onion_Shampoo_Survey.csv"), csvContent);

// 3. Aqualogica Radiance+ Dewy Watermelon Sunscreen Trial
const aquaData = [
  {
    Trial_ID: "AQ-TRL-801",
    Participant_Name: "Tanvi Gupta",
    Mobile: "+91 99100 44321",
    State: "Haryana",
    Trial_Batch: "Batch-Oct-Dewy",
    "Q1: Instant dewy glow & hydration feel?": "",
    "Q2: Sun protection efficacy outdoors?": "",
    "Q3: Texture absorption speed in high humidity?": ""
  },
  {
    Trial_ID: "AQ-TRL-802",
    Participant_Name: "Deepak Choudhary",
    Mobile: "+91 98290 55674",
    State: "Rajasthan",
    Trial_Batch: "Batch-Oct-Dewy",
    "Q1: Instant dewy glow & hydration feel?": "",
    "Q2: Sun protection efficacy outdoors?": "",
    "Q3: Texture absorption speed in high humidity?": ""
  }
];

const wsAqua = XLSX.utils.json_to_sheet(aquaData);
const wbAqua = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wbAqua, wsAqua, "Aqualogica_Trial");
XLSX.writeFile(wbAqua, path.join(samplesDir, "HONASA_Aqualogica_Watermelon_Trial.xlsx"));

console.log('Sample datasets generated successfully in ./samples');
