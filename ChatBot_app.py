from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import nltk 
from nltk.tokenize import word_tokenize
import re
nltk.download('punkt')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
df_mobiles=pd.read_csv("Mobiles.csv")
df_mobiles2=pd.read_csv("Mobiles.csv")
df_reviews=pd.read_csv("Reviews.csv")
# class Mobiles(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     Product_Id = db.Column(db.Integer)
#     Product_title=db.Column(db.String(200))
#     Product_Price=db.Column(db.String(30))
#     Product_Brand=db.Column(db.String(20))
#     Product_Rating=db.Column(db.String(10))
#     Reviews_text=db.column(db.String(500))
#     Reviews_Id=db.column(db.Integer)
# with app.app_context():
#     db.create_all()
#     # Mobiles.query.delete()
#     if not Mobiles.query.first():
#         mobile = Mobiles(
#                     Product_Id=df_mobiles['Product ID'],
#                     Product_title=df_mobiles['Product Title'],
#                     Product_Price=df_mobiles['Price'],
#                     Product_Brand=df_mobiles['Brand'],
#                     Product_Rating=df_mobiles['Rating'],
#                     Reviews_text=df_reviews['Reviews'],
#                     Reviews_Id=df_reviews['Product Review'],
#                 )
#         db.session.add(mobile)

#         db.session.commit()

# @app.route('/Records', methods=['GET'])
# def Records():
#     mobile = Mobiles.query.all()
#     return render_template('Records.html', mobile=mobile)  


@app.route("/")
def index():
    df_mobiles2['Price'] = pd.to_numeric(df_mobiles2['Price'].replace('[\D]', '', regex=True))
    listings=len(df_mobiles['Product ID'])
    questions=df_reviews['Questions'].sum()
    avg_ratings=df_mobiles['Rating'].mean()
    avg_ratings = round(avg_ratings, 1)      # Rounding the decimal by 1 point
    avg_price = df_mobiles2['Price'].mean() if 'Price' in df_mobiles2.columns else 0
    top_5_phones_rating = df_mobiles2.sort_values(by='Rating', ascending=False).head(5)
    top_5_phones_price = df_mobiles2.nlargest(5, 'Price')
    top_5_phones_reviews=df_reviews.sort_values(by='Total Reviews', ascending=False).head(5)
    return render_template('Dashboard.html',
                           top_phones_rating=top_5_phones_rating,
                           top_phones_price=top_5_phones_price,
                           top_phones_reviews=top_5_phones_reviews,
                           listings=listings,
                           questions=questions,
                           ratings=avg_ratings,
                           price=avg_price)


@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    return get_Chat_response(input)


def get_Chat_response(text):
    response = ""

    # Handling in-between questions
    if "between" in text.lower():
        # Extracting numerical values from the text
        price = [int(digit) for digit in text.split() if digit.isdigit()]
        if len(price) == 2:
            response = f"Sure! Following are the products between Rs. {price[0]} and Rs. {price[1]}."
        if len(price) == 2:
            min_price, max_price = price
        else:
            min_price, max_price = None, None

        # Filter the products based on the price range
        filtered_products = df_mobiles2[(df_mobiles2["Price"] >= min_price) & (df_mobiles2["Price"] <= max_price)]

        # Iterate over the rows of the filtered_products DataFrame
        for index, row in filtered_products.iterrows():
            tokens = word_tokenize(row['Product Title'])

            # Format each token on a separate line and append to the response
            response += f"{row['Brand']} - {row['Price']}\n"
            response += '\n'.join(tokens) + '<br/>\n\n'
            
    # Handling best phones
    elif "best" in text.lower():
        words = text.split()
        flag=0
        result=0
        normalized_num=0
        for word in words:
            if (word[-1] == 'K' and word[:-1].isdigit()) or (word[-1] == 'k' and word[:-1].isdigit()):
                # If "K" before an integer is found, multiply the integer by 1000
                normalized_num = int(word[:-1])
                result = normalized_num * 1000
                flag=1
        if flag==1: 
            if "under" in text.lower() or "below" in text.lower(): 
                min_rating=4.0;
                best_phones = best_phones_under_criteria(result,min_rating)
                if best_phones:
                    response = f"Based on user ratings and price, the best phones under Rs. {result} with a rating of {min_rating} or above are {'<br/> '.join(best_phones)}."+'<br/>'
                else:
                    response = f"Sorry, no phones were found under {price} with a rating of {min_rating} or above."
            elif "above" in text.lower() or "over" in text.lower():
                min_rating=4.0;
                best_phones = best_phones_above_criteria(result,min_rating)
                if best_phones:
                    response = f"Based on user ratings and price, the best phones above Rs. {result} with a rating of {min_rating} or above are {'<br/> '.join(best_phones)}."
                else:
                    response = f"Sorry, no phones were found above {result} with a rating of {min_rating} or above."
        else:
            price = [int(digit) for digit in text.split() if digit.isdigit()]
            if "under" in text.lower() or "below" in text.lower(): 
                min_rating=4.0;
                best_phones = best_phones_under_criteria(price[0],min_rating)
                if best_phones:
                    response = f"Based on user ratings and price, the best phones under Rs. {price[0]} with a rating of {min_rating} or above are {'<br/> '.join(best_phones)}."
                else:
                    response = f"Sorry, no phones were found under {price} with a rating of {min_rating} or above."
            elif "above" in text.lower() or "over" in text.lower():
                min_rating=4.0;
                best_phones = best_phones_above_criteria(price[0],min_rating)
                if best_phones:
                    response = f"Based on user ratings and price, the best phones above Rs. {price[0]} with a rating of {min_rating} or above are {'<br/> '.join(best_phones)}."
                    response += '\n'+ '<br/>\n\n'
                else:
                    response = f"Sorry, no phones were found above {price} with a rating of {min_rating} or above."
    
    # Handling price questions
    elif "under" in text.lower() or "over" in text.lower() or "above" in text.lower() or "below" in text.lower():
        words = text.split()
        flag=0
        for word in words:
            if (word[-1] == 'K' and word[:-1].isdigit()) or (word[-1] == 'k' and word[:-1].isdigit()):
                # If "K" before an integer is found, multiply the integer by 1000
                number_before_k = int(word[:-1])
                result = number_before_k * 1000
                flag=1
        if flag==1: 
            if "under" in text or "below" in text:
                num = result
                filtered_products = df_mobiles[df_mobiles['Price'].apply(lambda x: int(''.join(char for char in x if char.isdigit())) < num)]
                response = f"Sure! Following are the products under Rs. {result}:\n\n"

                # Iterate over the rows of the filtered_products DataFrame
                for index, row in filtered_products.iterrows():
                    tokens = word_tokenize(row['Product Title'])

                    response += f"{row['Brand']} - {row['Price']}\n"
                    response += '\n'.join(tokens) + '<br/>\n\n'
                
            elif "over" in text or "above" in text:
                num = result
                filtered_products = df_mobiles[df_mobiles['Price'].apply(lambda x: int(''.join(char for char in x if char.isdigit())) > num)]
                response = f"Sure! Following are the products above Rs. {result}:\n\n"
                # Iterate over the rows of the filtered_products DataFrame
                for index, row in filtered_products.iterrows():
                    tokens = word_tokenize(row['Product Title'])

                    response += f"{row['Brand']} - {row['Price']}\n"
                    response += '\n'.join(tokens) + '<br/>\n\n'
                else:
                    response += f"Sorry! There are no products above Rs. {result}:\n\n"
        else:
            price = [int(digit) for digit in text.split() if digit.isdigit()]
            if "under" in text or "below" in text:
                num = price[0]
                filtered_products = df_mobiles[df_mobiles['Price'].apply(lambda x: int(''.join(char for char in x if char.isdigit())) < num)]
                response = f"Sure! Following are the products under Rs. {price[0]}:\n\n"

                # Iterate over the rows of the filtered_products DataFrame
                for index, row in filtered_products.iterrows():
                    tokens = word_tokenize(row['Product Title'])

                    response += f"{row['Brand']} - {row['Price']}\n"
                    response += '\n'.join(tokens) + '<br/>\n\n'
            
            elif "over" in text or "above" in text:
                num = price[0]
                filtered_products = df_mobiles[df_mobiles['Price'].apply(lambda x: int(''.join(char for char in x if char.isdigit())) > num)]
                response = f"Sure! Following are the products above Rs. {price[0]}:\n\n"

                # Iterate over the rows of the filtered_products DataFrame
                for index, row in filtered_products.iterrows():
                    tokens = word_tokenize(row['Product Title'])

                    response += f"{row['Brand']} - {row['Price']}\n"
                    response += '\n'.join(tokens) + '<br/>\n\n'
    
    elif "hello" in text.lower() or "hey" in text.lower() or "hi" in text.lower():
        response="Hello! I am your personal Chatbot! Ask me anything about the products on Daraz."
    
    elif "bye" in text.lower() or "goodbye" in text.lower() or "good bye" in text.lower():
        response="Goodbye! (˶ᵔ ᵕ ᵔ˶)."

    else:
        response = "Sorry, I didn't understand that! (´•︵•`)"
    
        

    return response

# Helper Functions
def best_phones_under_criteria(price_limit, min_rating):
    best_phones = []
    for index,row in df_mobiles.iterrows():
        price_str = row['Price'].replace('Rs. ', '').replace(',', '')
        price = float(price_str)
        rating = float(row['Rating'])
        
        if price <= price_limit and rating >= min_rating:
            best_phones.append(row['Product Title'])
    
    return best_phones

def best_phones_above_criteria(price_limit, min_rating):
    best_phones = []
    for index,row in df_mobiles.iterrows():
        price_str = row['Price'].replace('Rs. ', '').replace(',', '')
        price = float(price_str)
        rating = float(row['Rating'])
        
        if price >= price_limit and rating >= min_rating:
            best_phones.append(row['Product Title'])
    
    return best_phones

if __name__ == '__main__':
    app.run(debug=True)
