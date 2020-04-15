"""WORKING WITH CATEGORIES"""
from typing import Dict, List, NamedTuple

import db


class Category(NamedTuple):
    """Structure of category"""
    codename: str
    name: str
    is_base_expense: bool
    aliases: List[str]


class Categories:
    def __init__(self):
        self._categories = self._load_categories()

    def _load_categories(self) -> List[Category]:
        """Returns a reference of expense categories from the database """
        categories = db.fetchall(
            "category", "codename name is_base_expense aliases".split()
        )
        categories = self._fill_aliases(categories)
        return categories

    def _fill_aliases(self, categories: List[Dict]) -> List[Category]:
        """Fills aliases for each category, that is, possible names
        of this category that we can write in the body of the message.
        For example, the category “cafe” can be written as cafe,
        restaurant, etc."""
        categories_result = []
        for index, category in enumerate(categories):
            aliases = category["aliases"].split(",")
            aliases = list(filter(None, map(str.strip, aliases)))
            aliases.append(category["codename"])
            aliases.append(category["name"])
            categories_result.append(Category(
                codename=category['codename'],
                name=category['name'],
                is_base_expense=category['is_base_expense'],
                aliases=aliases
            ))
        return categories_result

    def get_all_categories(self) -> List[Category]:
        """Returns a reference of categories"""
        return self._categories

    def get_category(self, category_name: str) -> Category:
        """Returns a category for one of its aliases"""
        found = None
        other_category = None
        for category in self._categories:
            if category.codename == "other":
                other_category = category
            for alias in category.aliases:
                if category_name in alias:
                    found = category
        if not found:
            found = other_category
        return found
