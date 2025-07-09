import pandas as pd
import os
file_path=(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\customer\Customer list.xlsx")
def read_file(file_path, skiprows=0):
    """
    Reads a file and returns a DataFrame. Supports CSV, Excel, and TXT files.
    
    Parameters:
        file_path (str): Path to the file.
        skiprows (int): Number of rows to skip at the top of the file.
    
    Returns:
        pd.DataFrame: Loaded data.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        return pd.read_csv(file_path, skiprows=skiprows)
    elif ext in ['.xls', '.xlsx']:
        return pd.read_excel(file_path, skiprows=skiprows)
    elif ext == '.txt':
        return pd.read_csv(file_path, delimiter='\t', skiprows=skiprows)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
cu = read_file(file_path,skiprows=5)
print(cu.head())

# transform the values into title format
cu.columns=cu.columns.str.strip().str.title()
cu.dropna(how='all',inplace=True)

# field mapping 
customer_mapping = {
    "Reference":"Name",
    "Business Address":"Street",
    "Postal Address":"Ship Street",
    "Web":"WWW",
    "Abn":"ABN"
}
cu=cu.rename(columns=customer_mapping)

# now add new columns that
cu['Type']='Customer'
cu['Status']='Active'
cu['Ship City']=pd.NA
cu['Ship State']=pd.NA
cu['Ship Postcode']=pd.NA
cu['Ship Country']=pd.NA
cu['city']=pd.NA
cu['State']=pd.NA
cu['Postcode']=pd.NA
cu['Country']=pd.NA
cu['Contact ID']=['C'+'-'+str(i)for i in range(1,len(cu)+1)]
cu["Balance ($)"]=pd.NA
# removing '-' from fax column 
cu["Fax"]=cu["Fax"].replace('-',pd.NA)
cu["ABN"]=cu["ABN"].replace('-',pd.NA)



columns_order=["Contact ID","Name","Phone","Type","Email","Balance ($)","Status","Street","City","State","Podcast","Country","Ship Street",
"Ship City","Ship State","Ship Postcode","Ship Country","ABN","Fax","WWW"]
final_columns = [col for col in columns_order if col in cu.columns]
cu = cu[final_columns]

# new file output
cu.to_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\customer\MYOB-Customer.xlsx",sheet_name='Customers',index=False)

# checking if any syntax error 
print("Conversion successful!")

