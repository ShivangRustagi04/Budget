# expense_tracker.py
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Set page config
st.set_page_config(page_title="💰 AI Expense Tracker", layout="centered")

# Title
st.title("💰 Personal Expense Tracker with Gemini AI")

# Initialize session state
if 'expenses' not in st.session_state:
    if os.path.exists('expenses.json'):
        try:
            with open('expenses.json', 'r') as f:
                st.session_state.expenses = json.load(f)
        except Exception as e:
            st.warning(f"Could not load saved data: {e}")
            st.session_state.expenses = []
    else:
        st.session_state.expenses = []

# --- Save Expenses ---
def save_expenses():
    with open('expenses.json', 'w') as f:
        json.dump(st.session_state.expenses, f, indent=2)

# --- Input Form ---
st.header("➕ Add New Expense")
with st.form("expense_form"):
    amount = st.number_input("Amount ($)", min_value=0.0, step=0.5)
    category = st.selectbox(
        "Category",
        ["Food", "Rent", "Travel", "Entertainment", "Utilities", "Other"]
    )
    expense_date = st.date_input("Date", value=datetime.today())
    submitted = st.form_submit_button("Add Expense")

    if submitted and amount > 0:
        new_expense = {
            "amount": amount,
            "category": category,
            "date": str(expense_date)
        }
        st.session_state.expenses.append(new_expense)
        save_expenses()
        st.success(f"✅ Added ${amount:.2f} for {category}")

# --- Display & Analyze Expenses ---
if st.session_state.expenses:
    st.header("📊 Your Expenses")

    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.expenses)
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year

    # Time filter
    timeframe = st.radio("View by:", ["Weekly", "Monthly"], horizontal=True)

    if timeframe == "Weekly":
        grouped = df.groupby(['year', 'week', 'category'])['amount'].sum().reset_index()
        total_spent = df['amount'].sum()
    else:
        grouped = df.groupby(['year', 'month', 'category'])['amount'].sum().reset_index()
        total_spent = df['amount'].sum()

    st.subheader("Summary Table")
    st.dataframe(grouped, use_container_width=True)

    st.subheader("Total Spending")
    st.metric("Total", f"${total_spent:,.2f}")

    # Bar chart
    st.bar_chart(grouped.set_index('category')['amount'])

    # --- AI Insights Using Gemini ---
    st.header("🧠 Gemini Financial Advice")

    prompt = f"""
    You are a friendly personal finance advisor. Here's a user's spending data:

    {df.to_string(index=False)}

    Total spent: ${total_spent:.2f}
    Top category: {df.groupby('category')['amount'].sum().idxmax()}
    Most frequent category: {df['category'].mode()[0] if len(df) > 0 else 'N/A'}

    Give one short, encouraging tip to improve their budgeting.
    Keep it under 2 sentences. Be kind and practical!
    """

    ai_advice = None

    if os.getenv("GEMINI_API_KEY"):
        try:
            # Choose model
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            # Extract text
            if response.candidates and len(response.candidates) > 0:
                ai_advice = response.candidates[0].content.parts[0].text.strip()
            else:
                ai_advice = "Gemini didn't return a response. Try again."

        except Exception as e:
            ai_advice = f"⚠️ AI error: {str(e)}. Check your API key or internet connection."
    else:
        # Fallback logic
        top_cat = df.groupby('category')['amount'].sum().idxmax()
        perc = (df[df['category'] == top_cat]['amount'].sum() / total_spent) * 100
        if perc > 50:
            ai_advice = f"You're spending {perc:.1f}% on {top_cat}. Consider setting a weekly limit!"
        else:
            ai_advice = "Spending looks balanced! Keep building healthy habits."

    # Display AI advice
    st.info(f"💬 {ai_advice}")

    # Clear all data
    if st.button("🗑️ Clear All Expenses"):
        st.session_state.expenses = []
        if os.path.exists('expenses.json'):
            os.remove('expenses.json')
        st.rerun()

else:
    st.info("No expenses yet. Add one above!")

# Footer
st.markdown("---")
st.caption("✨ Built with Streamlit + Gemini AI | Track smarter, spend wiser.")