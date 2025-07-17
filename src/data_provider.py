
from .upsell_data import INSURANCE_PLANS, ACCESSORIES, WATCHES

class DataProvider:
    """
    A class to simulate fetching data from a database or API.
    In this version, it loads data from the local upsell_data.py file.
    """

    def get_insurance_plans(self):
        """Returns all available insurance plans."""
        return INSURANCE_PLANS

    def get_accessories(self):
        """Returns all available accessories."""
        return ACCESSORIES

    def get_watches(self):
        """Returns all available watches."""
        return WATCHES

# Create a singleton instance of the data provider
data_provider = DataProvider() 