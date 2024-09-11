import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

# Constants
API_BASE_URL = "https://explorer.unisat.io/fractal-mainnet/api/address/summary"
REFRESH_INTERVAL = 30  # seconds

# Function to fetch account data from Unisat API
def fetch_account_data(address):
    try:
        response = requests.get(f"{API_BASE_URL}/{address}")
        response.raise_for_status()
        data = response.json()
        balance = data.get('balance', 0) / 100000000  # Convert satoshis to BTC
        return {'address': address, 'balance': balance}
    except requests.RequestException as e:
        st.error(f"Error fetching data for address {address}: {str(e)}")
        return None

# Function to update account data
def update_accounts_data(accounts):
    updated_data = []
    for account in accounts:
        data = fetch_account_data(account)
        if data:
            updated_data.append(data)
    return updated_data

# Streamlit app
def main():
    st.set_page_config(page_title="Crypto Account Balance Dashboard", layout="wide")
    st.title("Cryptocurrency Account Balance Dashboard")

    # Initialize session state for accounts
    if 'accounts' not in st.session_state:
        st.session_state.accounts = []

    # Add new account
    with st.sidebar:
        st.header("Add New Account")
        new_account = st.text_input("Enter Bitcoin address")
        if st.button("Add Account"):
            if new_account and new_account not in st.session_state.accounts:
                st.session_state.accounts.append(new_account)
                st.success(f"Account {new_account} added successfully!")
            elif new_account in st.session_state.accounts:
                st.warning("This account is already in the list.")
            else:
                st.warning("Please enter a valid Bitcoin address.")

    # Main content
    if not st.session_state.accounts:
        st.info("Add Bitcoin addresses using the sidebar to start tracking balances.")
    else:
        # Fetch and display account data
        account_data = update_accounts_data(st.session_state.accounts)
        
        if account_data:
            df = pd.DataFrame(account_data)
            
            # Display data in a table
            st.subheader("Account Balances")
            st.dataframe(df.style.format({'balance': '{:.8f}'}), width=800)

            # Create a bar chart of account balances
            fig = px.bar(df, x='address', y='balance', title="Account Balance Distribution")
            fig.update_layout(xaxis_title="Bitcoin Address", yaxis_title="Balance (BTC)")
            st.plotly_chart(fig, use_container_width=True)

        # Add a placeholder for refreshing data
        placeholder = st.empty()

        # Refresh data every 30 seconds
        refresh_counter = 0
        while True:
            time.sleep(1)
            refresh_counter += 1
            
            if refresh_counter >= REFRESH_INTERVAL:
                account_data = update_accounts_data(st.session_state.accounts)
                if account_data:
                    df = pd.DataFrame(account_data)
                    with placeholder.container():
                        st.dataframe(df.style.format({'balance': '{:.8f}'}), width=800)
                        fig = px.bar(df, x='address', y='balance', title="Account Balance Distribution")
                        fig.update_layout(xaxis_title="Bitcoin Address", yaxis_title="Balance (BTC)")
                        st.plotly_chart(fig, use_container_width=True)
                refresh_counter = 0
            
            # Update the refresh countdown
            placeholder.text(f"Next refresh in {REFRESH_INTERVAL - refresh_counter} seconds")

if __name__ == "__main__":
    main()
