import pandas as pd

df = pd.read_csv("TCB_RobotChatDetail.csv")

df_customer = df[df['message_from'] == 0]
df_customer = df_customer.drop_duplicates(subset=['message'])
df_customer['message'].to_csv("backend/CustomerChat.csv")