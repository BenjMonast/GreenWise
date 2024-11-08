# Inspiration
People are increasingly aware of climate change but lack actionable steps. Everything in life has a carbon cost, but it's difficult to understand, measure, and mitigate. Information about carbon footprints of products is often inaccessible for the average consumer, and alternatives are time consuming to research and find.

# What it does
With GreenWise, you can link email or upload receipts to analyze your purchases and suggest products with lower carbon footprints. By tracking your carbon usage, it helps you understand and improve your environmental impact. It provides detailed insights, recommends sustainable alternatives, and facilitates informed choices.

# How we built it
We started by building a tool that utilizes computer vision to read information off of a receipt, an API to gather information about the products, and finally ChatGPT API to categorize each of the products. We also set up an alternative form of gathering information in which the user forwards digital receipts to a unique email.

Once we finished the process of getting information into storage, we built a web scraper to gather the carbon footprints of thousands of items for sale in American stores, and built a database that contains these, along with AI-vectorized form of the product's description.

Vectorizing the product titles allowed us to quickly judge the linguistic similarity of two products by doing a quick mathematical operation. We utilized this to make the application compare each product against the database, identifying products that are highly similar with a reduced carbon output.

This web application was built with a Python Flask backend and Bootstrap for the frontend, and we utilize ChromaDB, a vector database that allowed us to efficiently query through vectorized data.

# Accomplishments that we're proud of
In 24 hours, we built a fully functional web application that uses real data to provide real actionable insights that allow users to reduce their carbon footprint
