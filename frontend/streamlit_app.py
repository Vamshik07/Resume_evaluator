#!/usr/bin/env python3
import os
import streamlit as st
from dashboard import main as dashboard_main

def install_spacy_model():
    try:
        import spacy
        spacy.load("en_core_web_sm")
        print("✅ spaCy model ready")
    except Exception as e:
        print("❌ spaCy model error:", e)

def main():
    print("🎯 Resume Evaluation System - Streamlit Deployment")
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs(".streamlit", exist_ok=True)
    
    # Just run the dashboard
    dashboard_main()

if __name__ == "__main__":
    install_spacy_model()
    main()
