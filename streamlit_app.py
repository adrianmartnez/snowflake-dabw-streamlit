import streamlit as st
import requests
import pandas as pd
from urllib.parse import quote
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input("Name on Smoothie:")

st.write("The name on your Smoothie will be:", name_on_order)

session = st.connection("snowflake").session()

my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(col("FRUIT_NAME"), col("SEARCH_ON"))

pd_df = my_dataframe.to_pandas()

fruit_names = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_names,
    max_selections=5
)

if ingredients_list:
    ingredients_string = "".join(ingredients_list)

    st.write(ingredients_string)

    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write(
            "The search value for ",
            fruit_chosen,
            " is ",
            search_on,
            "."
        )

        st.subheader(f"{fruit_chosen} Nutrition Information")

        try:
            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/" + quote(
                    fruit_chosen,
                    safe=""
                ),
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

        except requests.HTTPError as error:
            if smoothiefroot_response.status_code == 404:
                st.warning(
                    f"Nutrition information not found for {fruit_chosen}."
                )
            else:
                st.warning(
                    f"API error for {fruit_chosen}: {error}"
                )

        except requests.RequestException as error:
            st.warning(
                f"Could not retrieve nutrition data for {fruit_chosen}: {error}"
            )

        except (ValueError, TypeError) as error:
            st.warning(
                f"Invalid nutrition data for {fruit_chosen}: {error}"
            )

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
