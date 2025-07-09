# "D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\Supplier\Supplier list.xlsx"
import pandas as pd
import os
from config import get_file

file_path=(get_file("SUPPLIER_LIST_FILE"))
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
su = read_file(file_path,skiprows=5)
print(su.head())

# transform the values into title format
su.columns=su.columns.str.strip().str.title()
su.dropna(how='all',inplace=True)

# field mapping 
customer_mapping = {
    "Reference":"Name",
    "Business Address":"Street",
    "Postal Address":"Postcode",
    "Web":"WWW",
    "Abn":"ABN"
}
su=su.rename(columns=customer_mapping)

# now add new columns that
su['Type']='Supplier'
su['Status']='Active'
su['Ship City']=pd.NA
su['Ship State']=pd.NA
su['Ship Postcode']=pd.NA
su['Ship Country']=pd.NA
su['city']=pd.NA
su['State']=pd.NA
su['Postcode']=pd.NA
su['Country']=pd.NA
su["Balance ($)"]=pd.NA
su['Contact ID']=['S'+'-'+str(i)for i in range(1,len(su)+1)]

# removing '-' from fax column 
su["Fax"]=su["Fax"].replace('-',pd.NA)
su["ABN"]=su["ABN"].replace('-',pd.NA)
su["WWW"]=su["WWW"].replace('-',pd.NA)
su["Email"]=su["Email"].replace('-',pd.NA)
su["Street"]=su["Street"].replace('-',pd.NA)



columns_order=["Contact ID","Name","Phone","Type","Email","Balance ($)","Status","Street","City","State","Podcast","Country","Ship Street",
"Ship City","Ship State","Ship Postcode","Ship Country","ABN","Fax","WWW"]
final_columns = [col for col in columns_order if col in su.columns]
su = su[final_columns]

# new file output
su.to_excel(get_file("MYOB_SUPPLIER"),sheet_name='Supplier',index=False)

# checking if any syntax error 
print("Conversion successful!")


