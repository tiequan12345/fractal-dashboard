import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime
import logging
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
API_BASE_URL = "https://explorer.unisat.io/fractal-mainnet/api/address/summary"
REFRESH_INTERVAL = 30  # seconds

# Function to load addresses from file
def load_addresses():
    try:
        with open('addresses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save addresses to file
def save_addresses(addresses):
    with open('addresses.json', 'w') as f:
        json.dump(addresses, f)

# Function to fetch account data from Unisat API
def fetch_account_data(address):
    logging.info(f"Fetching data for address: {address}")
    try:
        response = requests.get(f"{API_BASE_URL}?address={address}")
        response.raise_for_status()
        data = response.json()
        
        # Debug logging
        logging.debug(f"Raw API response for address {address}: {data}")
        
        # Check if 'data' is in the response
        if 'data' not in data:
            logging.error(f"'data' field not found in API response for address {address}")
            return None
        
        # Check if 'balance' is in the 'data' object
        if 'balance' not in data['data']:
            logging.error(f"'balance' field not found in 'data' object for address {address}")
            return None
        
        balance = data['data']['balance'] / 100000000  # Convert satoshis to BTC
        logging.info(f"Successfully extracted balance for {address}: {balance} BTC")
        return {'address': address, 'balance': balance}
    except requests.RequestException as e:
        logging.error(f"Error fetching data for address {address}: {str(e)}")
        return None

# Function to update account data
def update_accounts_data(accounts):
    logging.info(f"Updating data for {len(accounts)} accounts")
    updated_data = []
    for account in accounts:
        data = fetch_account_data(account)
        if data:
            updated_data.append(data)
    logging.info(f"Updated data: {updated_data}")
    return updated_data

# Streamlit app
def main():
    logging.info("Starting Streamlit app")
    st.set_page_config(page_title="Crypto Account Balance Dashboard", layout="wide")
    st.title("Cryptocurrency Account Balance Dashboard")

    # Initialize session state for accounts and balance history
    if 'accounts' not in st.session_state:
        st.session_state.accounts = load_addresses()
    if 'balance_history' not in st.session_state:
        st.session_state.balance_history = {account: [] for account in st.session_state.accounts}

    # Add new account
    with st.sidebar:
        st.header("Add New Account")
        new_account = st.text_input("Enter Bitcoin address")
        if st.button("Add Account"):
            if new_account and new_account not in st.session_state.accounts:
                st.session_state.accounts.append(new_account)
                st.session_state.balance_history[new_account] = []
                save_addresses(st.session_state.accounts)  # Save to file
                logging.info(f"Added new account: {new_account}")
                st.success(f"Account {new_account} added successfully!")
            elif new_account in st.session_state.accounts:
                st.warning("This account is already in the list.")
            else:
                st.warning("Please enter a valid Bitcoin address.")

    # Display current accounts with delete buttons
    st.sidebar.header("Manage Accounts")
    for account in st.session_state.accounts:
        cols = st.sidebar.columns([3, 1])
        cols[0].write(account)
        if cols[1].button("Delete", key=f"delete_{account}"):
            st.session_state.accounts.remove(account)
            del st.session_state.balance_history[account]
            save_addresses(st.session_state.accounts)  # Save to file
            st.sidebar.success(f"Account {account} deleted successfully!")
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

    # Main content
    if not st.session_state.accounts:
        st.info("Add Bitcoin addresses using the sidebar to start tracking balances.")
    else:
        # Fetch and display account data
        logging.info("Fetching account data")
        account_data = update_accounts_data(st.session_state.accounts)
        logging.info(f"Fetched account data: {account_data}")
        
        if account_data:
            df = pd.DataFrame(account_data)
            
            # Update balance history
            current_time = datetime.now()
            for data in account_data:
                address = data['address']
                balance = data['balance']
                st.session_state.balance_history[address].append((current_time, balance))
            
            logging.info(f"Updated balance history: {st.session_state.balance_history}")
            
            # Display data in a table
            st.subheader("Account Balances")
            st.dataframe(df.style.format({'balance': '{:.8f}'}), width=800)

            # Create a bar chart of account balances
            logging.info("Creating bar chart")
            fig_bar = px.bar(df, x='address', y='balance', title="Account Balance Distribution")
            fig_bar.update_layout(xaxis_title="Bitcoin Address", yaxis_title="Balance (BTC)")
            st.plotly_chart(fig_bar, use_container_width=True)
            logging.info("Bar chart created and displayed")

            # Create a line chart of balance changes over time
            logging.info("Creating line chart")
            fig_line = go.Figure()
            for address in st.session_state.balance_history:
                history = st.session_state.balance_history[address]
                if history:
                    times, balances = zip(*history)
                    fig_line.add_trace(go.Scatter(x=times, y=balances, mode='lines+markers', name=address))
            
            fig_line.update_layout(
                title="Balance Changes Over Time",
                xaxis_title="Time",
                yaxis_title="Balance (BTC)",
                legend_title="Bitcoin Address"
            )
            st.plotly_chart(fig_line, use_container_width=True)
            logging.info("Line chart created and displayed")

        # Add a placeholder for refreshing data
        placeholder = st.empty()

        # Refresh data every 30 seconds
        refresh_counter = 0
        while True:
            time.sleep(1)
            refresh_counter += 1
            
            if refresh_counter >= REFRESH_INTERVAL:
                logging.info("Refreshing data")
                account_data = update_accounts_data(st.session_state.accounts)
                if account_data:
                    df = pd.DataFrame(account_data)
                    current_time = datetime.now()
                    for data in account_data:
                        address = data['address']
                        balance = data['balance']
                        st.session_state.balance_history[address].append((current_time, balance))
                    
                    logging.info(f"Refreshed balance history: {st.session_state.balance_history}")
                    
                    with placeholder.container():
                        st.dataframe(df.style.format({'balance': '{:.8f}'}), width=800)
                        logging.info("Updating bar chart")
                        fig_bar = px.bar(df, x='address', y='balance', title="Account Balance Distribution")
                        fig_bar.update_layout(xaxis_title="Bitcoin Address", yaxis_title="Balance (BTC)")
                        st.plotly_chart(fig_bar, use_container_width=True)
                        logging.info("Bar chart updated")
                        
                        logging.info("Updating line chart")
                        fig_line = go.Figure()
                        for address in st.session_state.balance_history:
                            history = st.session_state.balance_history[address]
                            if history:
                                times, balances = zip(*history)
                                fig_line.add_trace(go.Scatter(x=times, y=balances, mode='lines+markers', name=address))
                        
                        fig_line.update_layout(
                            title="Balance Changes Over Time",
                            xaxis_title="Time",
                            yaxis_title="Balance (BTC)",
                            legend_title="Bitcoin Address"
                        )
                        st.plotly_chart(fig_line, use_container_width=True)
                        logging.info("Line chart updated")
                
                refresh_counter = 0
            
            # Update the refresh countdown
            placeholder.text(f"Next refresh in {REFRESH_INTERVAL - refresh_counter} seconds")

if __name__ == "__main__":
    main()
