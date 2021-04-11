import numpy as np 
import pandas as pd

#It became apparent from prior attempts that the dataset is too big to handle for my little computer, so let's cut out unnecessasry columns,
#these columns being order_id (unique to every row) and page_id (which is also largely unique save for "order" page, but I can distinguish
#order through other means like target)

#only take columns we need
columns = ['user_id', 'product', 'site_version', 'time','title', 'target']
print(columns)

#load dataframe from file I saved to desktop
df1 = pd.read_csv(r'C:\Users\11150049982565796543\Desktop\product.csv', delimiter=',', usecols=columns)

#memory is going to be an issue here, so let's investigate
df1.dtypes 
df1.memory_usage().sum() / (1024**2)
#ouch, a lot of data. Let's if we can cut it down a bit
df1[['product','site_version','title']] = df1[['product','site_version','title']].astype('category')
df1[['user_id']] = df1[['user_id']].astype('string')
#not bad, cut it down by about 33%

#check values
df1.head(5)
df1.info()
df1.select_dtypes('object').nunique()

#I think I have the info we need, now let's break it down by questions.

#Q1) Find every instance of a product that was bought before a banner view.
#Create a list of every user that has a confirmed product purchase.
df_abr = df1[['user_id', 'target']]

df_buyers = df_abr[df_abr.target == 1]
df_buyers_list = df_buyers.user_id.tolist()

#Now use that list to isolate users who actually bought products

df_only_purchasers = df1[df1['user_id'].isin(df_buyers_list)]

#check that some known users are in the dataframe successfully
'000298d8a61b4f7b0fe5c7fd3d8c4c9c' in df_only_purchasers.user_id.values #true
'0070bde13bc9f816d50206c3cab57cca' in df_only_purchasers.user_id.values #true
'00731f619e3d27117f673dfd659ac700' in df_only_purchasers.user_id.values #true
'0075d30900bdafead95769eafa1bdd44' in df_only_purchasers.user_id.values #false 
'00ad4321b2f29236a79b37b6338c7b6c' in df_only_purchasers.user_id.values #true 

#There have been 248722 purchases in this data set. Including banner clicks and banner views, there is 999312 rows of data
#for people who ended up purchasing somthing

df_only_purchasers.head(30)
#from this we can see that it is ordered by user_id, then title, then time. Let's order it by user_id --> time

df_only_purchasers = df_only_purchasers.sort_values(['user_id', 'time'])

# Since it's now ordered by time, let's us do a simple trick to see who bought what first

df_first_action = df_only_purchasers.drop_duplicates(subset = ['user_id'], keep = 'first')
df_first_action.head(30)

#This has 237866 purchasers. It's different from the value before (248722) because that was total number of purchases,
#including people who bought multiple products

double_ups = 248722 - 237866

#4.36% of all purchases were a multi-buy from one individual

#Excellent! Now, let's sum the target values

first_buy = df_first_action.target.sum()
total_purchases = len(df_buyers_list)
total_buyers = len(df_first_action)

#A shocking result!!! 96,317 purchases on the website happened before anyone had seen or clicked on a banner ad. This represents
#38% of all total purchases, and 40.5% of total buyers

#we can double check that this seems correct by checking a sample of known users who ordered first
df_only_purchasers.loc[df_only_purchasers['user_id'] == '00025258be954956b0af7b2e910f196c']
df_only_purchasers.loc[df_only_purchasers['user_id'] == '000279810d7bb4889653c3560ae0a6a3']
df_only_purchasers.loc[df_only_purchasers['user_id'] == '0005a43df9f360f49da45c7317e57ba4']
df_only_purchasers.loc[df_only_purchasers['user_id'] == '00067f82984cf29385fee7465c1e979b']
#All look good to me.

#Q3) Likelihood of purchasing depending on number of banner shows - is there an assossiation between number of banner views and whether
#a product was purchased?
#This will be a fun one. Banner clicks are irrelevent for this question as each banner click is matched to a banner view,
#so we'll only care about banner views.

#only actually need user_id, title.
df1_abb2 = df1[['user_id', 'title']]

#The trick here is to make banner clicks = 0, banner views = 1+, and orders 100+. That way, we can sum the values and
#parse them to break down by views and total orders.
conditions = [(df1_abb2['title'] == 'banner_show'), (df1_abb2['title'] == 'banner_click'), (df1_abb2['title'] == 'order')]
values = [1, 0, 100]

#make the values clearly distinguishable from one another
df1_abb2['banner_conversion'] = np.select(conditions, values)

#now group by user_id
df1_abb3 = df1_abb2[['user_id', 'banner_conversion']]
df1_grouped = df1_abb3.groupby('user_id').banner_conversion.sum()

#my computer has been crashing, so for safety let's print out as a csv
df1_grouped.to_csv(r'C:\Users\11150049982565796543\Desktop\grouped_product.csv')

total_users = len(df1_grouped)

#As an aside, only 5.8% of unique users actually ended up buying anything...

df1_grouped_final = df1_grouped['user_id']
df1_grouped_final.head(5)

#What follows are some methods to help with the memory use

columns1 = ['banner_conversion']
df1_grouped_final = pd.read_csv(r'C:\Users\11150049982565796543\Desktop\grouped_product.csv', delimiter=',', usecols=columns1)

df1_grouped_final[['banner_conversion']] = df1_grouped_final[['banner_conversion']].astype('string')

#we now want to be able to break the column into categories. Turning it into a list will be helpful
df1_grouped_final_list = df1_grouped_final.banner_conversion.tolist()

new_list = []

#This is to standardise the columns so everything has 3 characters
for i in df1_grouped_final_list:
    if len(i) == 3:
        new_list.append(i)
    elif len(i) == 2:
        new_list.append('0' + i)
    else:
        new_list.append('00' + i)

new_list_categories = []
new_list_order_made = []

for j in new_list:
    new_list_categories.append(j[1:])
    new_list_order_made.append(j[0])

#Now we have all the info we need to summarise our data into categories

category_set = sorted(set(new_list_categories))

#There are 14 categories of banner views, 0 - 14
converted_ints = [int(m) for m in new_list_order_made]

zippy = zip(new_list_categories, converted_ints)
zip_list = list(zippy)

occurences= []

for k in category_set:
    val = new_list_categories.count(k)
    occurences.append(val)

def group_by(my_list):
    result = {}
    for k, v in my_list:
        result[k] = v if k not in result else result[k] + v
    return result 

final_vals = (group_by(zip_list))

#We finally have our values, {'01': 95636, '02': 58392, '03': 41456, 
# 11': 1362, '05': 11640, '08': 1852, '04': 13275, '07': 8745, '06': 9706, 
# '12': 1302, '10': 1559, '09': 1665, '13': 1076, '14': 1056, '00': 0}
#Let's combine these with the occurences from before and graph in excel to save time.

#Q2) Evidence as to whether there is a funnel from views --> clicks --> purchasing.
#We'll try different times: 6 hours (most believable), 24 hours (possible) and 120 hours (unlikely)

df_abr_4 = df1[['user_id', 'product', 'time', 'title']]

#This code is for if you quit out between sessions...
# df_abr = df1[['user_id', 'target']]
# df_buyers = df_abr[df_abr.target == 1]
# df_buyers_list = df_buyers.user_id.tolist()

df_only_purchasers = df_abr_4[df_abr_4['user_id'].isin(df_buyers_list)]

df_only_purchasers.to_csv(r'C:\Users\11150049982565796543\Desktop\purchase_users.csv')

#Then finish it off in excel since it'll be quicker that way.