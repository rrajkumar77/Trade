import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(page_title="Trading Recommendation System", layout="wide")

# Sample stock data
@st.cache_data
def load_stock_data():
    data = {
        'symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT'],
        'name': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.', 'Amazon.com Inc.', 'Tesla Inc.',
                'Meta Platforms Inc.', 'NVIDIA Corp.', 'JPMorgan Chase & Co.', 'Visa Inc.', 'Walmart Inc.'],
        'current_price': [178.72, 402.56, 165.62, 175.90, 237.49, 450.12, 860.26, 182.43, 276.84, 62.54],
        'pe': [29.4, 34.8, 25.7, 47.2, 68.5, 25.9, 62.1, 11.9, 31.2, 27.3],
        'market_cap': [2760, 3100, 2150, 1820, 754, 1150, 2120, 525, 570, 780],
        'growth': [8.1, 14.3, 11.5, 9.8, 21.2, 13.7, 30.2, 4.3, 7.5, 3.9],
        'volatility': ['Medium', 'Low', 'Medium', 'High', 'Very High', 'Medium', 'High', 'Low', 'Low', 'Very Low']
    }
    return pd.DataFrame(data)

# Generate historical price data for a stock
def generate_historical_data(start_price, volatility, days=30):
    data = []
    price = start_price
    
    # Volatility factor
    vol_factor = {
        'Very Low': 0.4,
        'Low': 0.7,
        'Medium': 1.0,
        'High': 1.4,
        'Very High': 1.8
    }[volatility]
    
    for i in range(days, -1, -1):
        date = datetime.now() - timedelta(days=i)
        
        # Add some randomness to price changes
        change = (np.random.random() - 0.5) * 2 * vol_factor
        price = price * (1 + change / 100)
        
        data.append({
            'date': date,
            'price': round(price, 2)
        })
    
    return pd.DataFrame(data)

# Calculate feasibility score
def calculate_feasibility_score(stock):
    # Basic algorithm to calculate feasibility
    # In a real app, this would be much more sophisticated
    pe_score = 20 if stock['pe'] < 30 else 15 if stock['pe'] < 40 else 10 if stock['pe'] < 50 else 5
    growth_score = stock['growth'] * 3
    
    volatility_scores = {
        'Very Low': 20,
        'Low': 15,
        'Medium': 10,
        'High': 5,
        'Very High': 0
    }
    volatility_score = volatility_scores[stock['volatility']]
    
    return pe_score + growth_score + volatility_score

# Determine recommended investment amount
def calculate_investment_amount(total_funds, score, max_percentage=10):
    # Higher score = higher percentage of funds (up to max_percentage)
    percentage_to_invest = min((score / 100) * max_percentage, max_percentage)
    return round(total_funds * percentage_to_invest / 100, 2)

# Recommend holding period
def recommend_holding_period(volatility, growth):
    if volatility == 'Very High':
        return 'Short-term (1-3 months)'
    if volatility == 'High':
        return 'Medium-term (3-6 months)' if growth > 15 else 'Short-term (1-3 months)'
    if volatility == 'Medium':
        return 'Medium-term (3-6 months)' if growth > 10 else 'Long-term (6-12 months)'
    return 'Long-term (6-12+ months)'

# Calculate stop loss price
def calculate_stop_loss(current_price, volatility):
    stop_loss_percentage = {
        'Very Low': 5,
        'Low': 7,
        'Medium': 10,
        'High': 15,
        'Very High': 20
    }[volatility]
    
    return round(current_price * (1 - stop_loss_percentage / 100), 2)

# Main application
def main():
    st.title("Trading Recommendation System")
    
    # Sidebar for user inputs
    st.sidebar.header("Configuration")
    available_funds = st.sidebar.number_input("Available Funds ($)", min_value=1000.0, max_value=1000000.0, value=10000.0, step=1000.0)
    
    # Load stock data
    stock_data = load_stock_data()
    
    # Calculate analysis results
    results = []
    for _, stock in stock_data.iterrows():
        score = calculate_feasibility_score(stock)
        results.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'current_price': stock['current_price'],
            'pe': stock['pe'],
            'market_cap': stock['market_cap'],
            'growth': stock['growth'],
            'volatility': stock['volatility'],
            'score': score,
            'recommended_amount': calculate_investment_amount(available_funds, score),
            'hold_period': recommend_holding_period(stock['volatility'], stock['growth']),
            'stop_loss': calculate_stop_loss(stock['current_price'], stock['volatility'])
        })
    
    # Convert to DataFrame and sort by score
    results_df = pd.DataFrame(results).sort_values(by='score', ascending=False)
    
    # Layout with two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Trade Recommendations")
        
        # Format the table display
        formatted_df = results_df[['symbol', 'name', 'score']].copy()
        formatted_df.columns = ['Symbol', 'Company', 'Score']
        
        # Use Streamlit's dataframe with selection
        selection = st.dataframe(
            formatted_df,
            height=400,
            use_container_width=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    help="Feasibility score out of 100",
                    format="%d/100",
                    min_value=0,
                    max_value=100,
                ),
            },
            hide_index=True
        )
        
        # Get selected stock
        selected_stock_index = st.selectbox(
            "Select a stock for detailed analysis:",
            options=list(range(len(results_df))),
            format_func=lambda x: f"{results_df.iloc[x]['symbol']} - {results_df.iloc[x]['name']}",
        )
        
        selected_stock = results_df.iloc[selected_stock_index]
    
    with col2:
        if selected_stock is not None:
            st.subheader(f"{selected_stock['name']} ({selected_stock['symbol']})")
            st.metric("Current Price", f"${selected_stock['current_price']}")
            
            # Generate and display historical data
            hist_data = generate_historical_data(
                selected_stock['current_price'],
                selected_stock['volatility']
            )
            
            # Create price chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_data['date'],
                y=hist_data['price'],
                mode='lines',
                name='Price',
                line=dict(color='royalblue', width=2)
            ))
            fig.update_layout(
                title='30-Day Price History',
                xaxis_title='Date',
                yaxis_title='Price ($)',
                height=300,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Create metrics for the selected stock
            metrics_col1, metrics_col2 = st.columns(2)
            with metrics_col1:
                st.metric("Feasibility Score", f"{int(selected_stock['score'])}/100")
                st.metric("Recommended Investment", f"${selected_stock['recommended_amount']}")
            
            with metrics_col2:
                st.metric("Recommended Hold Period", selected_stock['hold_period'])
                st.metric("Stop Loss Price", f"${selected_stock['stop_loss']}")
            
            # Additional info
            st.subheader("Analysis Summary")
            
            score_assessment = (
                "strong potential" if selected_stock['score'] > 60 else
                "moderate potential" if selected_stock['score'] > 40 else
                "limited potential"
            )
            
            volatility_assessment = (
                "Low volatility makes it suitable for more conservative investors." 
                if selected_stock['volatility'] in ['Low', 'Very Low'] else
                "Medium volatility suggests balanced risk/reward profile." 
                if selected_stock['volatility'] == 'Medium' else
                "High volatility indicates higher risk but potential for greater returns."
            )
            
            allocation_percentage = round(selected_stock['recommended_amount'] / available_funds * 100, 1)
            
            st.info(
                f"{selected_stock['symbol']} shows {score_assessment} based on its current metrics. "
                f"{volatility_assessment} Recommended allocation represents a {allocation_percentage}% "
                f"position in your portfolio."
            )
            
            # Financial metrics detail
            st.subheader("Financial Metrics")
            metrics_data = {
                'Metric': ['P/E Ratio', 'Market Cap (billions)', 'Annual Growth (%)', 'Volatility'],
                'Value': [
                    selected_stock['pe'],
                    selected_stock['market_cap'],
                    f"{selected_stock['growth']}%",
                    selected_stock['volatility']
                ]
            }
            st.table(pd.DataFrame(metrics_data))

if __name__ == "__main__":
    main()
