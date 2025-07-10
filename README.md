# 🤖 AI-Powered Procurement Assistant

An advanced, end-to-end procurement workflow application powered by a microservices architecture. This tool streamlines the process from generating a Request for Quote (RFQ) to creating a final Purchase Order (PO), using AI for document generation, data extraction, and analysis.

## Features

-   **💬 AI-Powered RFQ Generation**: Use a chatbot interface to define procurement needs and generate a professional, structured RFQ document.
-   **📄 Intelligent Data Extraction**: Upload vendor quotations (PDF, JPG, PNG) and automatically extract key information like line items, prices, and terms using the AgentQL API.
-   **🔍 AI Vendor Analysis**: Leverage OpenAI's GPT-4 to perform a comprehensive analysis of all vendor quotations, providing a clear recommendation and a detailed comparison report.
-   **📋 Automated Purchase Order Creation**: Generate a professional Purchase Order for the selected vendor based on the initial RFQ and final analysis.
-   **📤 PDF & Data Export**: Download all generated documents (RFQ, Comparison Table, PO) as formatted PDFs. Export the entire workflow data as a single JSON file.
-   **🔗 Webhook Integration**: Push the complete procurement data to any external system or webhook for seamless integration.

## Architecture Overview

This application is built using a **microservices architecture** to ensure scalability, maintainability, and separation of concerns. The system consists of a Streamlit frontend and three dedicated backend services for handling business logic, data extraction, and PDF generation.

For a detailed explanation, see the [Architecture Guide](#architecture-guide).

## Prerequisites

Before you begin, ensure you have the following installed:
-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/)

## 🚀 Setup & Installation

Follow these steps to get the application running locally.

**1. Clone the Repository**
```bash
git clone <your-repository-url>
cd ai-procurement-microservices