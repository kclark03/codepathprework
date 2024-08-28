import csv
import sqlite3
import db_base as db

class Recipe:
    def __init__(self, row, category_id):
        self.name = row[0]
        self.category_id = category_id

class Ingredient:
    def __init__(self, ingredient_str, recipe_id):
        # Parses the ingredient string and combines quantity and name
        name, quantity = self.parse_ingredient(ingredient_str)
        self.quantity_ingredient = f"{quantity} {name}"
        self.recipe_id = recipe_id

    def parse_ingredient(self, ingredient_str):
        # Improved parsing, assuming the format "quantity name"
        parts = ingredient_str.split(' ', 1)
        if len(parts) > 1:
            quantity = parts[0].strip()
            name = parts[1].strip()
        else:
            quantity = ''
            name = parts[0].strip()
        return name, quantity

class RecipeDB(db.DBbase):
    def __init__(self, db_name):
        super().__init__(db_name)
        self.recipe_list = []
        self.ingredient_list = []
        self.category_map = {}

    def reset_or_create_db(self):
        try:
            sql = """
                DROP TABLE IF EXISTS category;
                DROP TABLE IF EXISTS recipes;
                DROP TABLE IF EXISTS ingredients;

                CREATE TABLE category (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                );

                CREATE TABLE recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES category(id)
                );

                CREATE TABLE ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quantity_ingredient TEXT,
                    recipe_id INTEGER,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
                );
            """
            self.execute_script(sql)
            print("Database tables created successfully.")
        except Exception as e:
            print("Error creating tables:", e)

    def read_recipe_data(self, file_name):
        self.recipe_list = []
        self.category_map = {}
        try:
            with open(file_name, 'r') as record:
                csv_contents = csv.reader(record, delimiter=',')
                headers = next(csv_contents)
                print("CSV Headers:", headers)

                for row in csv_contents:
                    if len(row) < 3:
                        print("Skipping invalid row:", row)
                        continue

                    recipe_name = row[0]
                    category_name = row[1]
                    ingredients = row[2].split(',')

                    # Handle category
                    if category_name not in self.category_map:
                        self.category_map[category_name] = None  # This will be updated with the ID later

                    # Temporarily store the recipe and its associated category and ingredients
                    self.recipe_list.append((recipe_name, category_name, ingredients))

            print("Data read successfully from file.")
        except Exception as e:
            print("Error reading file:", e)

    def save_to_database(self):
        print("Number of records to save:", len(self.recipe_list))
        save = input("Continue? (y/n): ").lower().strip()
        if save == "y":
            cursor = self.get_cursor
            connection = self.get_connection

            # Save categories and get IDs
            for category_name in self.category_map.keys():
                cursor.execute("INSERT INTO category (name) VALUES (?)", (category_name,))
                self.category_map[category_name] = cursor.lastrowid
            connection.commit()

            # Save recipes and ingredients
            for recipe_name, category_name, ingredients in self.recipe_list:
                category_id = self.category_map[category_name]
                cursor.execute("INSERT INTO recipes (name, category_id) VALUES (?, ?)", (recipe_name, category_id))
                recipe_id = cursor.lastrowid

                for ingredient_str in ingredients:
                    ingredient = Ingredient(ingredient_str, recipe_id)
                    cursor.execute("INSERT INTO ingredients (quantity_ingredient, recipe_id) VALUES (?, ?)", (ingredient.quantity_ingredient, recipe_id))
                connection.commit()

            print("Data saved to database successfully.")
        else:
            print("Save to DB aborted")

    def add_recipe(self, name, category):
        # First, ensure the category exists and get its ID
        category_id = self.get_category_id(category)
        if category_id is None:
            print("Category does not exist. Please add the category first.")
            return
        try:
            self.get_cursor.execute("INSERT INTO recipes (name, category_id) VALUES (?, ?)",
                                    (name, category_id))
            self.get_connection.commit()
            print("Recipe added successfully!")
        except Exception as e:
            print("Error adding recipe:", e)

    def delete_recipe(self, recipe_id):
        try:
            self.get_cursor.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
            self.get_connection.commit()
            print("Recipe deleted successfully!")
        except Exception as e:
            print("Error deleting recipe:", e)

    def update_recipe(self, recipe_id, new_name=None, new_category=None):
        try:
            if new_name:
                self.get_cursor.execute("UPDATE recipes SET name=? WHERE id=?", (new_name, recipe_id))
            if new_category:
                category_id = self.get_category_id(new_category)
                self.get_cursor.execute("UPDATE recipes SET category_id=? WHERE id=?", (category_id, recipe_id))
            self.get_connection.commit()
            print("Recipe updated successfully!")
        except Exception as e:
            print("Error updating recipe:", e)

    def get_category_id(self, category_name):
        try:
            self.get_cursor.execute("SELECT id FROM category WHERE name=?", (category_name,))
            result = self.get_cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting category ID for {category_name}: {e}")
            return None


def user_interface():
    db_instance = RecipeDB("recipes.sqlite")
    db_instance.reset_or_create_db()
    db_instance.read_recipe_data("recipes.csv")
    db_instance.save_to_database()

    while True:
        print("Welcome to 'Dish Directory'")
        main_entry = input("Please select an option below:"
                           "\n- Recipe Management - "
                           "\n- Quit - ").lower()

        if main_entry == "quit":
            print("Quitting the program.")
            break
        elif main_entry == "recipe management":
            recipe_management_menu(db_instance)
        else:
            print("Invalid entry, please try again.")

def recipe_management_menu(db_instance):
    while True:
        recipe_action = input("Recipe Management Options:"
                              "\n- Add Recipe - "
                              "\n- Delete Recipe - "
                              "\n- Update Recipe - "
                              "\n- Read Recipe Data - "
                              "\n- Return - ").lower()
        if recipe_action == "return":
            break
        elif recipe_action == "add recipe":
            name = input("Enter recipe name: ")
            category = input("Enter recipe category: ")
            db_instance.add_recipe(name, category)
        elif recipe_action == "delete recipe":
            recipe_id = int(input("Enter recipe ID to delete: "))
            db_instance.delete_recipe(recipe_id)
        elif recipe_action == "update recipe":
            recipe_id = int(input("Enter recipe ID to update: "))
            new_name = input("Enter new recipe name (leave blank to keep unchanged): ").strip() or None
            new_category = input("Enter new recipe category (leave blank to keep unchanged): ").strip() or None
            db_instance.update_recipe(recipe_id, new_name, new_category)
        elif recipe_action == "read recipe data":
            file_name = input("Enter CSV file name: ")
            print(db_instance.read_recipe_data(file_name))

if __name__ == "__main__":
    user_interface()






