import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input("Name on Smoothie:")

st.write("The name on your Smoothie will be:", name_on_order)

session = st.connection("snowflake").session()

my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(col("FRUIT_NAME"))

fruit_names = [
    row["FRUIT_NAME"]
    for row in my_dataframe.collect()
]

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

if ingredients_list:
    ingredients_string = "".join(ingredients_list)

    st.write(ingredients_string)

    if st.button("Submit Order"):
        if not name_on_order.strip():
            st.error("Please enter a name for your order.")
        elif len(name_on_order.strip()) > 100:
            st.error("The name is too long.")
        else:
            session.sql(
                """
                INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                    (INGREDIENTS, NAME_ON_ORDER)
                VALUES (?, ?)
                """,
                params=[
                    ingredients_string,
                    name_on_order.strip()
                ]
            ).collect()

            st.success(
                "Your Smoothie is ordered, " + name_on_order + "!",
                icon="✅"
            )

# SmoothieFroot API
st.subheader("SmoothieFroot API - Watermelon")

try:
    smoothiefroot_response = requests.get(
        "https://my.smoothiefroot.com/api/fruit/watermelon",
        timeout=15
    )

    st.text(smoothiefroot_response)

    smoothiefroot_response.raise_for_status()

    smoothiefroot_data = smoothiefroot_response.json()

    st.json(smoothiefroot_data)

    sf_df = pd.json_normalize(smoothiefroot_data)

    st.dataframe(
        sf_df,
        use_container_width=True
    )

except requests.RequestException as error:
    st.error(f"SmoothieFroot API error: {error}")

except ValueError as error:
    st.error(f"Invalid API JSON response: {error}")
