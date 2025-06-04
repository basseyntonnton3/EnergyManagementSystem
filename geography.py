"""
Geographical data structure for the weather section.
Contains hierarchical data for continents, countries, and states.
"""

CONTINENTS = {
    "Africa": {
        "countries": {
            "Nigeria": {
                "states": [
                    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno",
                    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT", "Abuja",
                    "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi",
                    "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo",
                    "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara"
                ]
            },
            "South Africa": {
                "states": [
                    "Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal", "Limpopo",
                    "Mpumalanga", "Northern Cape", "North West", "Western Cape"
                ]
            },
            # Add more African countries as needed
        }
    },
    "Asia": {
        "countries": {
            "China": {
                "states": [
                    "Beijing", "Shanghai", "Guangdong", "Sichuan", "Hunan", "Henan",
                    "Zhejiang", "Anhui", "Fujian", "Jiangsu", "Shandong", "Hubei"
                ]
            },
            "India": {
                "states": [
                    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
                    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
                    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
                    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
                ]
            },
            # Add more Asian countries as needed
        }
    },
    "Europe": {
        "countries": {
            "France": {
                "states": [
                    "Île-de-France", "Auvergne-Rhône-Alpes", "Hauts-de-France", "Provence-Alpes-Côte d'Azur",
                    "Occitanie", "Nouvelle-Aquitaine", "Grand Est", "Pays de la Loire", "Bretagne",
                    "Normandie", "Bourgogne-Franche-Comté", "Centre-Val de Loire", "Corse"
                ]
            },
            "Germany": {
                "states": [
                    "Baden-Württemberg", "Bavaria", "Berlin", "Brandenburg", "Bremen",
                    "Hamburg", "Hesse", "Lower Saxony", "Mecklenburg-Vorpommern", "North Rhine-Westphalia",
                    "Rhineland-Palatinate", "Saarland", "Saxony", "Saxony-Anhalt",
                    "Schleswig-Holstein", "Thuringia"
                ]
            },
            # Add more European countries as needed
        }
    },
    "North America": {
        "countries": {
            "United States": {
                "states": [
                    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
                    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
                    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
                    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
                    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
                    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
                    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
                    "Wisconsin", "Wyoming"
                ]
            },
            "Canada": {
                "states": [
                    "Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador",
                    "Northwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island",
                    "Quebec", "Saskatchewan", "Yukon"
                ]
            },
            # Add more North American countries as needed
        }
    },
    "South America": {
        "countries": {
            "Brazil": {
                "states": [
                    "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", "Distrito Federal",
                    "Espírito Santo", "Goiás", "Maranhão", "Mato Grosso", "Mato Grosso do Sul",
                    "Minas Gerais", "Pará", "Paraíba", "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro",
                    "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia", "Roraima", "Santa Catarina",
                    "São Paulo", "Sergipe", "Tocantins"
                ]
            },
            "Argentina": {
                "states": [
                    "Buenos Aires", "Catamarca", "Chaco", "Chubut", "Córdoba", "Corrientes",
                    "Entre Ríos", "Formosa", "Jujuy", "La Pampa", "La Rioja", "Mendoza",
                    "Misiones", "Neuquén", "Río Negro", "Salta", "San Juan", "San Luis",
                    "Santa Cruz", "Santa Fe", "Santiago del Estero", "Tierra del Fuego",
                    "Tucumán"
                ]
            },
            # Add more South American countries as needed
        }
    },
    "Oceania": {
        "countries": {
            "Australia": {
                "states": [
                    "New South Wales", "Victoria", "Queensland", "Western Australia",
                    "South Australia", "Tasmania", "Australian Capital Territory",
                    "Northern Territory"
                ]
            },
            "New Zealand": {
                "states": [
                    "Auckland", "Bay of Plenty", "Canterbury", "Gisborne", "Hawke's Bay",
                    "Manawatu-Wanganui", "Marlborough", "Nelson", "Northland", "Otago",
                    "Southland", "Taranaki", "Waikato", "Wellington", "West Coast"
                ]
            },
            # Add more Oceanian countries as needed
        }
    }
}

def get_continents():
    """Return list of all continents."""
    return list(CONTINENTS.keys())

def get_countries(continent):
    """Return list of countries for a given continent."""
    if continent in CONTINENTS:
        return list(CONTINENTS[continent]["countries"].keys())
    return []

def get_states(continent, country):
    """Return list of states for a given country in a continent."""
    if continent in CONTINENTS and country in CONTINENTS[continent]["countries"]:
        return CONTINENTS[continent]["countries"][country]["states"]
    return [] 