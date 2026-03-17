import streamlit as st
import requests
import os
import pandas as pd

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

st.set_page_config(page_title="AI Stock Screener", layout="wide")
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

def login_user(email, password):
    """Login user and get token."""
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data['token']
            st.session_state.user_email = data['email']
            st.session_state.user_name = data['name']
            return True, "Login successful!"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Login failed')
            except:
                return False, f"Login failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running on http://127.0.0.1:8001"
    except requests.exceptions.JSONDecodeError:
        return False, "Server returned invalid response"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup_user(name, email, password):
    """Sign up new user and get token."""
    try:
        response = requests.post(f"{API_URL}/auth/signup", json={
            "name": name,
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data['token']
            st.session_state.user_email = data['email']
            st.session_state.user_name = data['name']
            return True, "Signup successful!"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Signup failed')
            except:
                return False, f"Signup failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running on http://127.0.0.1:8001"
    except requests.exceptions.JSONDecodeError:
        return False, "Server returned invalid response"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout_user():
    """Logout user and clear session."""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_email = None
    st.session_state.user_name = None

def run_screener(query):
    """Run stock screener with optimized error handling and caching."""
    if not query or not query.strip():
        return False, "Please enter a query"
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        with st.spinner("🔍 Analyzing your query..."):
            response = requests.post(f"{API_URL}/ai/screener", 
                                   params={"query": query.strip()}, 
                                   headers=headers,
                                   timeout=30)  
            
        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, dict):
                return False, "Invalid response format from server"
            if 'results' not in data:
                return False, "Missing results in server response"
            return True, data
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Invalid query')
            except:
                return False, "Invalid query format"
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return False, "Session expired. Please login again."
        elif response.status_code == 500:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Server error')
                if "Database query error" in error_detail:
                    return False, "Database connection issue. Please try again."
                return False, f"Server error: {error_detail}"
            except:
                return False, "Server error occurred"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', f'Backend error (status {response.status_code})')
            except:
                return False, f"Backend error (status {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "Query timed out. The database might be processing a complex request. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please check if the backend is running."
    except Exception as e:
        return False, f"Connection error: {str(e)}"

st.title("📊 AI Stock Screener")

def check_backend_connection():
    """Check if backend is running."""
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

if not check_backend_connection():
    st.error("⚠️ Backend server is not running!")
    st.info("Please start the FastAPI backend server:")
    st.code("uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload")
    st.stop()

if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both email and password")
    
    with tab2:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password", 
                                   help="Password should be 6-50 characters long")
            signup_button = st.form_submit_button("Sign Up")
            
            if signup_button:
                if name and email and password:
                    if len(name.strip()) == 0:
                        st.error("Please enter your full name")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                    elif len(password) > 50:
                        st.error("Password is too long (maximum 50 characters)")
                    elif '@' not in email:
                        st.error("Please enter a valid email address")
                    else:
                        success, message = signup_user(name.strip(), email.strip(), password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

else:
    col1, col2, col3 = st.columns([3, 0.5, 0.5])
    with col1:
        st.write(f"Welcome, {st.session_state.user_name}!")
    
    # Check for new alert notifications
    def get_new_notifications():
        """Get new alert notifications."""
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.get(f"{API_URL}/alerts/notifications", 
                                   params={"limit": 5}, 
                                   headers=headers)
            if response.status_code == 200:
                notifications = response.json()
                # Filter only new notifications (within last hour)
                return [n for n in notifications if n.get('status') == 'new']
            return []
        except:
            return []
    
    # Display compact notification bell
    new_notifications = get_new_notifications()
    with col2:
        if new_notifications:
            if st.button(f"🔔 {len(new_notifications)}", key="notification_bell", help=f"{len(new_notifications)} new alert(s)"):
                st.session_state.show_notifications = not st.session_state.get('show_notifications', False)
        else:
            st.button("🔔", key="notification_bell_empty", disabled=True, help="No new alerts")
    
    with col3:
        if st.button("Logout"):
            logout_user()
            st.rerun()
    
    # Show notifications popup if bell is clicked
    if st.session_state.get('show_notifications', False) and new_notifications:
        with st.expander("🔔 New Alerts", expanded=True):
            for notif in new_notifications:
                st.write(f"**{notif['symbol']}** triggered")
                st.caption(f"{notif['triggered_at']}")
            
            # Add refresh button
            if st.button("🔄 Refresh Alerts", key="refresh_notifications"):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    requests.post(f"{API_URL}/alerts/check", headers=headers)
                    st.rerun()
                except:
                    pass
    
    # Disclaimer banner
    st.info("⚠️ **Disclaimer:** This application is for educational and informational purposes only. The data, analysis, and recommendations provided should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions.")
    
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 Stock Screener", "💼 My Portfolios", "🔔 Price Alerts"])
    
    with tab1:
        st.warning("📊 **Stock Screener Disclaimer:** The screening results are based on historical data and should not be considered as investment recommendations. Past performance does not guarantee future results. Always conduct your own research before making investment decisions.")
        
        query = st.text_input(
            "Enter screening query",
            placeholder="e.g. PE ratio >= 5 and positive net profit for last 4 quarters",
            help="Try queries like 'Technology stocks with PE less than 20' or 'Large cap stocks with dividend yield above 2%'"
        )
        
        if st.button("Run Screener") and query:
            with st.spinner("Running screener..."):
                success, result = run_screener(query)
                
                if success:
                    result_count = len(result['results'])
                    st.success(f"Found {result_count} stocks matching your criteria")
                    
                    if result_count > 0:

                        st.subheader(f"Results ({result_count})")

                        import pandas as pd
                        df = pd.DataFrame(result["results"])
                        essential_columns = ['symbol', 'company_name', 'current_price', 'pe_ratio', 'market_cap', 'recommendation', 'upside_category']
                        available_columns = []
                        for col in essential_columns:
                            if col in df.columns:
                                available_columns.append(col)
                        df_display = df[available_columns] if available_columns else df
                        column_mapping = {
                            'symbol': 'Symbol',
                            'company_name': 'Company',
                            'pe_ratio': 'P/E',
                            'market_cap': 'Market Cap',
                            'current_price': 'Price',
                            'recommendation': 'Rating',
                            'upside_category': 'Upside Type'
                        }
                        
                        rename_dict = {k: v for k, v in column_mapping.items() if k in df_display.columns}
                        df_display = df_display.rename(columns=rename_dict)
                        
                        if 'P/E' in df_display.columns:
                            df_display['P/E'] = df_display['P/E'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) and x > 0 else "N/A")
                        if 'Market Cap' in df_display.columns:
                            df_display['Market Cap'] = df_display['Market Cap'].apply(lambda x: f"${x/1e9:.1f}B" if pd.notnull(x) and x > 0 else "N/A")
                        if 'Price' in df_display.columns:
                            df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) and x > 0 else "N/A")
                        
                        def style_upside_category(val):
                            if val == 'Strong Upside':
                                return 'background-color: #d4edda; color: #155724' 
                            elif val == 'Moderate Upside':
                                return 'background-color: #fff3cd; color: #856404' 
                            elif val == 'Target Below Price':
                                return 'background-color: #f8d7da; color: #721c24' 
                            return ''
                        
                        
                        if 'Upside Type' in df_display.columns:
                            styled_df = df_display.style.applymap(style_upside_category, subset=['Upside Type'])
                            st.dataframe(styled_df )
                        else:
                            st.dataframe(df_display )
                        
                        if result.get("has_quarterly", False) and result.get("quarterly_data"):
                            st.subheader("📊 Quarterly Financial Data")
                            
                            quarterly_data = result["quarterly_data"]
                            if quarterly_data and isinstance(quarterly_data, dict):
                        
                                symbols_with_data = []
                                for stock_id, quarters in quarterly_data.items():
                                    if quarters and isinstance(quarters, list) and len(quarters) > 0:
                                        if 'symbol' in quarters[0]:
                                            symbols_with_data.append(quarters[0]['symbol'])
                                
                                if symbols_with_data:
                                    if len(symbols_with_data) <= 5:
                                        tabs = st.tabs(symbols_with_data)
                                        
                                        for i, symbol in enumerate(symbols_with_data):
                                            with tabs[i]:
                                                symbol_quarters = None
                                                for stock_id, quarters in quarterly_data.items():
                                                    if quarters and len(quarters) > 0 and quarters[0].get('symbol') == symbol:
                                                        symbol_quarters = quarters
                                                        break
                                                
                                                if symbol_quarters:
                                                    try:
                                                        quarterly_df = pd.DataFrame(symbol_quarters)
                                                        required_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit']
                                                        available_cols = [col for col in required_cols if col in quarterly_df.columns]
                                                        
                                                        if available_cols:
                                                            quarterly_df = quarterly_df[available_cols]                                                        
                                                            for col in ['revenue', 'ebitda', 'net_profit']:
                                                                if col in quarterly_df.columns:
                                                                    quarterly_df[col] = quarterly_df[col].apply(
                                                                        lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
                                                                    )
                                                                    
                                                            col_mapping = {
                                                                'quarter': 'Quarter',
                                                                'year': 'Year', 
                                                                'revenue': 'Revenue',
                                                                'ebitda': 'EBITDA',
                                                                'net_profit': 'Net Profit'
                                                            }
                                                            quarterly_df = quarterly_df.rename(columns={k: v for k, v in col_mapping.items() if k in quarterly_df.columns})
                                                            st.dataframe(quarterly_df )
                                                        else:
                                                            st.warning(f"No quarterly data available for {symbol}")
                                                    except Exception as e:
                                                        st.error(f"Error displaying data for {symbol}: {str(e)}")
                                    else:
                                        for stock_id, quarters in quarterly_data.items():
                                            if quarters and len(quarters) > 0:
                                                symbol = quarters[0].get('symbol', f'Stock {stock_id}')
                                                with st.expander(f"📈 {symbol} - Quarterly Data"):
                                                    try:
                                                        quarterly_df = pd.DataFrame(quarters)
                                                        required_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit']
                                                        available_cols = [col for col in required_cols if col in quarterly_df.columns]
                                                        
                                                        if available_cols:
                                                            quarterly_df = quarterly_df[available_cols]                                                        
                                                            for col in ['revenue', 'ebitda', 'net_profit']:
                                                                if col in quarterly_df.columns:
                                                                    quarterly_df[col] = quarterly_df[col].apply(
                                                                        lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
                                                                    )
                                                            col_mapping = {
                                                                'quarter': 'Quarter',
                                                                'year': 'Year', 
                                                                'revenue': 'Revenue',
                                                                'ebitda': 'EBITDA',
                                                                'net_profit': 'Net Profit'
                                                            }
                                                            quarterly_df = quarterly_df.rename(columns={k: v for k, v in col_mapping.items() if k in quarterly_df.columns})
                                                            st.dataframe(quarterly_df )
                                                        else:
                                                            st.warning(f"No quarterly data available for {symbol}")
                                                    except Exception as e:
                                                        st.error(f"Error displaying data for {symbol}: {str(e)}")
                                else:
                                    st.info("No quarterly data available for the selected stocks")
                            else:
                                st.info("No quarterly data available")
                    
                    else:
                        st.info("No stocks matched your criteria")
                else:
                    error_msg = result
                    st.error(f"❌ {error_msg}")                
                    if "data we don't have" in error_msg.lower() or "unsupported" in error_msg.lower():
                        st.info("💡 Try: `PE ratio > 15` or `positive profit last 4 quarters`")
                    
                    if "Session expired" in result:
                        st.rerun()
    
    with tab2:
        st.warning("💼 **Portfolio Disclaimer:** Portfolio tracking is for educational and informational purposes only. The values shown are based on current market data and may not reflect actual trading prices. This tool does not provide investment advice or recommendations.")
        
        st.subheader("💼 Portfolio Management")
        def get_portfolios():
            """Get user's portfolios."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/portfolio/", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch portfolios"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_portfolio_holdings(portfolio_id):
            """Get holdings for a specific portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/portfolio/{portfolio_id}/holdings", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch holdings"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def create_portfolio(name):
            """Create a new portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.post(f"{API_URL}/portfolio/", 
                                       json={"name": name}, 
                                       headers=headers)
                if response.status_code == 200:
                    return True, "Portfolio created successfully"
                else:
                    return False, "Failed to create portfolio"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_portfolio_summary():
            """Get portfolio summary."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/portfolio/summary", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch summary"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        success, summary = get_portfolio_summary()
        if success:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Portfolios", summary.get('total_portfolios', 0))
            with col2:
                st.metric("Total Holdings", summary.get('total_holdings', 0))
            with col3:
                invested = summary.get('total_invested', 0)
                st.metric("Total Invested", f"${invested:,.2f}" if invested else "$0.00")
            with col4:
                current_value = summary.get('current_value', 0)
                st.metric("Current Value", f"${current_value:,.2f}" if current_value else "$0.00")
            
            if invested > 0:
                gain_loss = summary.get('total_gain_loss', 0)
                gain_loss_percent = summary.get('gain_loss_percent', 0)
                if gain_loss != 0:
                    st.metric("Total Gain/Loss", 
                             f"${gain_loss:+,.2f} ({gain_loss_percent:+.1f}%)",
                             delta=f"{gain_loss_percent:+.1f}%")
        
        st.divider()
        with st.expander("➕ Create New Portfolio"):
            with st.form("create_portfolio"):
                portfolio_name = st.text_input("Portfolio Name")
                if st.form_submit_button("Create Portfolio"):
                    if portfolio_name.strip():
                        success, message = create_portfolio(portfolio_name.strip())
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter a portfolio name")
        def add_holding(portfolio_id, stock_id, quantity, avg_price):
            """Add a holding to portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.post(f"{API_URL}/portfolio/{portfolio_id}/holdings",
                                       json={"stock_id": stock_id, "quantity": quantity, "avg_price": avg_price},
                                       headers=headers)
                if response.status_code == 200:
                    return True, "Holding added successfully"
                else:
                    return False, "Failed to add holding"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def update_holding(portfolio_id, holding_id, stock_id, quantity, avg_price):
            """Update a holding in portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.put(f"{API_URL}/portfolio/{portfolio_id}/holdings/{holding_id}",
                                       json={"stock_id": stock_id, "quantity": quantity, "avg_price": avg_price},
                                       headers=headers)
                if response.status_code == 200:
                    return True, "Holding updated successfully"
                else:
                    return False, "Failed to update holding"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def delete_holding(portfolio_id, holding_id):
            """Delete a holding from portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.delete(f"{API_URL}/portfolio/{portfolio_id}/holdings/{holding_id}",
                                         headers=headers)
                if response.status_code == 200:
                    return True, "Holding deleted successfully"
                else:
                    return False, "Failed to delete holding"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def delete_portfolio(portfolio_id):
            """Delete a portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.delete(f"{API_URL}/portfolio/{portfolio_id}", headers=headers)
                if response.status_code == 200:
                    return True, "Portfolio deleted successfully"
                else:
                    return False, "Failed to delete portfolio"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        success, portfolios = get_portfolios()
        if success and portfolios:
            st.subheader("Your Portfolios")
            
            for portfolio in portfolios:
                with st.expander(f"📁 {portfolio['name']} ({portfolio['total_holdings']} holdings - ${portfolio['total_value']:,.2f})"):
                    
                    # Add holding form
                    st.write("➕ Add New Holding")
                    
                    # Step 1: Search for stock
                    col_search1, col_search2 = st.columns([3, 1])
                    with col_search1:
                        search_symbol = st.text_input("Search Stock Symbol", key=f"search_{portfolio['portfolio_id']}", placeholder="e.g., AAPL, MSFT, GOOGL")
                    with col_search2:
                        st.write("")
                        st.write("")
                        search_btn = st.button("Search", key=f"search_btn_{portfolio['portfolio_id']}", use_container_width=True)
                    
                    # Store searched stock in session state
                    if search_btn and search_symbol.strip():
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.token}"}
                            response = requests.get(f"{API_URL}/portfolio/stocks/search",
                                                   params={"symbol": search_symbol.upper().strip()},
                                                   headers=headers)
                            if response.status_code == 200:
                                stock = response.json()
                                st.session_state[f"found_stock_{portfolio['portfolio_id']}"] = stock
                                st.success(f"✅ Found: {stock['symbol']} - {stock['company_name']}")
                            else:
                                st.error(f"Stock symbol '{search_symbol.upper()}' not found in database")
                                st.session_state[f"found_stock_{portfolio['portfolio_id']}"] = None
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            st.session_state[f"found_stock_{portfolio['portfolio_id']}"] = None
                    
                    # Step 2: Add holding form (shown only if stock is found)
                    found_stock = st.session_state.get(f"found_stock_{portfolio['portfolio_id']}")
                    if found_stock:
                        with st.form(f"add_holding_{portfolio['portfolio_id']}"):
                            st.write(f"**{found_stock['symbol']} - {found_stock['company_name']}**")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                quantity = st.number_input("Quantity", min_value=1, value=1, key=f"qty_{portfolio['portfolio_id']}")
                            with col2:
                                current_price = found_stock.get('current_price')
                                default_price = float(current_price) if current_price else 100.00
                                avg_price = st.number_input("Purchase Price", min_value=0.01, value=default_price, step=0.01, key=f"price_{portfolio['portfolio_id']}")
                                if current_price:
                                    st.caption(f"Current market price: ${current_price:.2f}")
                            with col3:
                                st.write("")
                                st.write("")
                                add_btn = st.form_submit_button("Add to Portfolio", use_container_width=True, type="primary")
                            
                            if add_btn:
                                success, message = add_holding(portfolio['portfolio_id'], found_stock['stock_id'], quantity, avg_price)
                                if success:
                                    st.success(message)
                                    # Clear the found stock
                                    st.session_state[f"found_stock_{portfolio['portfolio_id']}"] = None
                                    st.rerun()
                                else:
                                    st.error(message)
                    
                    st.divider()

                    # Display holdings
                    holdings_success, holdings = get_portfolio_holdings(portfolio['portfolio_id'])                    
                    if holdings_success and holdings:
                        st.write("📊 Holdings")
                        
                        for holding in holdings:
                            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
                            
                            with col1:
                                st.write(f"**{holding['symbol']}**")
                                st.caption(holding['company_name'][:30] + "..." if len(holding['company_name']) > 30 else holding['company_name'])
                            
                            with col2:
                                st.metric("Qty", holding['quantity'])
                            
                            with col3:
                                st.metric("Avg Price", f"${holding['avg_price']:.2f}")
                            
                            with col4:
                                current = holding.get('current_price')
                                st.metric("Current", f"${current:.2f}" if current else "N/A")
                            
                            with col5:
                                gain_loss = holding.get('gain_loss')
                                gain_loss_pct = holding.get('gain_loss_percent')
                                if gain_loss is not None and gain_loss_pct is not None:
                                    st.metric("Gain/Loss", f"${gain_loss:+,.2f}", delta=f"{gain_loss_pct:+.1f}%")
                                else:
                                    st.metric("Gain/Loss", "N/A")
                            
                            with col6:
                                # Edit/Delete buttons
                                edit_key = f"edit_{holding['holding_id']}"
                                delete_key = f"delete_{holding['holding_id']}"
                                
                                if st.button("✏️", key=edit_key, help="Edit holding"):
                                    st.session_state[f"editing_{holding['holding_id']}"] = True
                                    st.rerun()
                                
                                if st.button("🗑️", key=delete_key, help="Delete holding"):
                                    success, message = delete_holding(portfolio['portfolio_id'], holding['holding_id'])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            
                            # Edit form (shown when edit button is clicked)
                            if st.session_state.get(f"editing_{holding['holding_id']}", False):
                                with st.form(f"edit_form_{holding['holding_id']}"):
                                    st.write(f"Edit {holding['symbol']}")
                                    col_a, col_b, col_c = st.columns(3)
                                    with col_a:
                                        new_qty = st.number_input("New Quantity", min_value=1, value=holding['quantity'], key=f"edit_qty_{holding['holding_id']}")
                                    with col_b:
                                        new_price = st.number_input("New Avg Price", min_value=0.01, value=float(holding['avg_price']), step=0.01, key=f"edit_price_{holding['holding_id']}")
                                    with col_c:
                                        st.write("")
                                        st.write("")
                                        col_save, col_cancel = st.columns(2)
                                        with col_save:
                                            save_btn = st.form_submit_button("Save", use_container_width=True)
                                        with col_cancel:
                                            cancel_btn = st.form_submit_button("Cancel", use_container_width=True)
                                    
                                    if save_btn:
                                        success, message = update_holding(portfolio['portfolio_id'], holding['holding_id'], holding['stock_id'], new_qty, new_price)
                                        if success:
                                            st.session_state[f"editing_{holding['holding_id']}"] = False
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                                    
                                    if cancel_btn:
                                        st.session_state[f"editing_{holding['holding_id']}"] = False
                                        st.rerun()
                            
                            st.divider()
                    else:
                        st.info("No holdings in this portfolio. Add your first holding above!")
                    
                    # Delete portfolio button
                    st.write("")
                    if st.button(f"🗑️ Delete Portfolio '{portfolio['name']}'", key=f"del_port_{portfolio['portfolio_id']}", type="secondary"):
                        if st.session_state.get(f"confirm_delete_{portfolio['portfolio_id']}", False):
                            success, message = delete_portfolio(portfolio['portfolio_id'])
                            if success:
                                st.success(message)
                                st.session_state[f"confirm_delete_{portfolio['portfolio_id']}"] = False
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.session_state[f"confirm_delete_{portfolio['portfolio_id']}"] = True
                            st.warning("⚠️ Click again to confirm deletion. This will delete all holdings!")
                            st.rerun()
        else:
            st.info("No portfolios found. Create your first portfolio above!")

    
    with tab3:
        st.warning("🔔 **Price Alerts Disclaimer:** Price alerts are for informational purposes only and should not be considered as trading signals or investment advice. Alert triggers are based on available market data and may have delays. Always verify information independently before making any investment decisions.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("🔔 Price Alert Management")
        with col2:
            if st.button("🔄 Check Alerts Now", help="Manually check all alerts against current stock prices"):
                with st.spinner("Checking alerts..."):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.token}"}
                        response = requests.post(f"{API_URL}/alerts/check", headers=headers)
                        if response.status_code == 200:
                            result = response.json()
                            results = result.get('results', {})
                            triggered = results.get('triggered', 0)
                            if triggered > 0:
                                st.success(f"✅ Checked alerts! {triggered} alert(s) triggered.")
                            else:
                                st.info("✅ Checked alerts. No new triggers.")
                            st.rerun()
                        else:
                            st.error("Failed to check alerts")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        def get_alerts():
            """Get user's alerts."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/alerts/", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch alerts"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_alert_events():
            """Get alert events."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/alerts/events", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch alert events"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_alert_summary():
            """Get alert summary."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/alerts/summary", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch summary"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def create_alert(stock_id, portfolio_id, metric, operator, threshold):
            """Create a new alert."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.post(f"{API_URL}/alerts/", 
                                       json={"stock_id": stock_id, "portfolio_id": portfolio_id, "metric": metric, "operator": operator, "threshold": threshold}, 
                                       headers=headers)
                if response.status_code == 200:
                    return True, "Alert created successfully"
                else:
                    error_data = response.json()
                    return False, error_data.get('detail', 'Failed to create alert')
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def delete_alert(alert_id):
            """Delete an alert."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.delete(f"{API_URL}/alerts/{alert_id}", headers=headers)
                if response.status_code == 200:
                    return True, "Alert deleted successfully"
                else:
                    return False, "Failed to delete alert"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def toggle_alert(alert_id):
            """Toggle alert active status."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.patch(f"{API_URL}/alerts/{alert_id}/toggle", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to toggle alert"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_all_stocks():
            """Get all stocks for dropdown."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/alerts/stocks/list", headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    return []
            except:
                return []
        
        success, summary = get_alert_summary()
        if success:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Alerts", summary.get('total_alerts', 0))
            with col2:
                st.metric("Active Alerts", summary.get('active_alerts', 0))
            with col3:
                st.metric("Total Triggers", summary.get('total_triggers', 0))
            with col4:
                st.metric("Stocks Monitored", summary.get('stocks_monitored', 0))
        
        st.divider()
        
        with st.expander("➕ Create New Alert"):
            st.write("Set up alerts to monitor your portfolio stocks")
            
            with st.form("create_alert"):
                col1, col2 = st.columns(2)
                
                with col1:
                    stock_symbol = st.text_input("Stock Symbol (e.g., AAPL, TSLA)", key="alert_stock")
                    metric = st.selectbox("Metric", [
                        "price",
                        "pe_ratio",
                        "market_cap",
                        "eps",
                        "roe",
                        "dividend_yield"
                    ], format_func=lambda x: x.replace('_', ' ').title())
                    
                with col2:
                    operator = st.selectbox("Operator", [">", "<", ">=", "<=", "="])
                    threshold = st.number_input("Threshold Value", min_value=0.0, step=0.01, format="%.2f")
                
                portfolios_success, portfolios = get_portfolios()
                if portfolios_success and portfolios:
                    portfolio_options = {p['name']: p['portfolio_id'] for p in portfolios}
                    selected_portfolio_name = st.selectbox("Portfolio", list(portfolio_options.keys()))
                    selected_portfolio_id = portfolio_options[selected_portfolio_name]
                else:
                    st.warning("You need to create a portfolio first")
                    selected_portfolio_id = None
                
                if st.form_submit_button("Create Alert"):
                    if stock_symbol.strip() and threshold > 0 and selected_portfolio_id:
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.token}"}
                            response = requests.get(f"{API_URL}/alerts/stocks/search", 
                                                   params={"symbol": stock_symbol.upper().strip()},
                                                   headers=headers)
                            if response.status_code == 200:
                                stock = response.json()
                                success, message = create_alert(stock['stock_id'], selected_portfolio_id, metric, operator, threshold)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error(f"Stock symbol '{stock_symbol.upper()}' not found")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.error("Please fill in all fields and select a portfolio")
        
        success, alerts = get_alerts()
        if success and alerts:
            st.subheader("Your Active Alerts")
            
            alerts_df = pd.DataFrame(alerts)            
            if 'selected' not in st.session_state:
                st.session_state.selected = []
            
            selection_data = []
            for idx, alert in enumerate(alerts):
                alert_key = f"{alert['alert_id']}"
                is_selected = alert_key in st.session_state.selected
                
                # Check if triggered recently (within last hour)
                is_new_trigger = False
                last_triggered_display = "Never"
                if pd.notnull(alert['last_triggered']):
                    last_triggered_time = pd.to_datetime(alert['last_triggered'])
                    time_diff = pd.Timestamp.now() - last_triggered_time
                    is_new_trigger = time_diff.total_seconds() < 3600  # Within 1 hour
                    last_triggered_display = last_triggered_time.strftime('%Y-%m-%d %H:%M')
                    if is_new_trigger:
                        last_triggered_display = f"🆕 {last_triggered_display}"
                
                selection_data.append({
                    'Select': is_selected,
                    'alert_id': alert['alert_id'],
                    'Symbol': alert['symbol'],
                    'Company': alert['company_name'],
                    'Metric': alert['metric'].replace('_', ' ').title(),
                    'Op': alert['operator'],
                    'Threshold': f"{alert['threshold']:,.2f}",
                    'Active': '✅' if alert['is_active'] else '❌',
                    'Last Triggered': last_triggered_display
                })
            
            edited_df = st.data_editor(
                pd.DataFrame(selection_data),
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select alerts to manage",
                        default=False,
                    ),
                    "alert_id": None,  
                },
                disabled=["Symbol", "Company", "Metric", "Op", "Threshold", "Active", "Last Triggered"],
                hide_index=True,
                use_container_width=True
            )
            
            st.session_state.selected = [
                str(row['alert_id']) for _, row in edited_df.iterrows() if row['Select']
            ]
            
            if st.session_state.selected:
                st.subheader(f"Manage Selected Alerts ({len(st.session_state.selected)} selected)")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗑️ Delete Selected", use_container_width=True):
                        deleted_count = 0
                        for alert_id in st.session_state.selected:
                            success, message = delete_alert(int(alert_id))
                            if success:
                                deleted_count += 1
                        st.session_state.selected = []
                        st.success(f"Deleted {deleted_count} alert(s)")
                        st.rerun()
                
                with col2:
                    if st.button("🔔 Activate Selected", use_container_width=True):
                        activated_count = 0
                        for alert_id in st.session_state.selected:
                            alert = next((a for a in alerts if a['alert_id'] == int(alert_id)), None)
                            if alert and not alert['is_active']:
                                success, result = toggle_alert(int(alert_id))
                                if success:
                                    activated_count += 1
                        st.session_state.selected = []
                        st.success(f"Activated {activated_count} alert(s)")
                        st.rerun()
                
                with col3:
                    if st.button("🔕 Deactivate Selected", use_container_width=True):
                        deactivated_count = 0
                        for alert_id in st.session_state.selected:
                            alert = next((a for a in alerts if a['alert_id'] == int(alert_id)), None)
                            if alert and alert['is_active']:
                                success, result = toggle_alert(int(alert_id))
                                if success:
                                    deactivated_count += 1
                        st.session_state.selected = []
                        st.success(f"Deactivated {deactivated_count} alert(s)")
                        st.rerun()
        else:
            st.info("No alerts found. Create your first alert above!")
        
        st.divider()
        
        st.subheader("📊 Recent Alert Triggers")
        success, events = get_alert_events()
        if success and events:
            events_df = pd.DataFrame(events)
            
            display_columns = ['symbol', 'company_name', 'metric', 'operator', 'threshold', 'triggered_value', 'triggered_at']
            available_event_columns = [col for col in display_columns if col in events_df.columns]
            
            if available_event_columns:
                events_display = events_df[available_event_columns].copy()
                
                column_mapping = {
                    'symbol': 'Symbol',
                    'company_name': 'Company',
                    'metric': 'Metric',
                    'operator': 'Op',
                    'threshold': 'Threshold',
                    'triggered_value': 'Actual Value',
                    'triggered_at': 'Triggered At'
                }
                
                events_display = events_display.rename(columns={k: v for k, v in column_mapping.items() if k in events_display.columns})
                
                if 'Metric' in events_display.columns:
                    events_display['Metric'] = events_display['Metric'].apply(lambda x: x.replace('_', ' ').title() if pd.notnull(x) else "N/A")
                
                if 'Threshold' in events_display.columns:
                    events_display['Threshold'] = events_display['Threshold'].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "N/A")
                if 'Actual Value' in events_display.columns:
                    events_display['Actual Value'] = events_display['Actual Value'].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "N/A")
                
                if 'Triggered At' in events_display.columns:
                    events_display['Triggered At'] = events_display['Triggered At'].apply(
                        lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else "N/A"
                    )
                
                st.dataframe(events_display, use_container_width=True)
            else:
                st.info("No event data available")
        else:
            st.info("No alert triggers yet")
