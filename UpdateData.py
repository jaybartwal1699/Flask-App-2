import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch MongoDB URI from environment variables
mongo_uri = os.getenv('MONGODB_URI')


def fetch_data_from_mongo():
    try:
        # Connect to MongoDB Atlas using the URI from environment variable
        client = MongoClient(mongo_uri)
        db = client['EduGuide']  # Database name
        collection = db['CollegeData']  # Collection name

        # Fetch all data from the collection
        data = list(collection.find())

        if not data:
            print("No data found in the collection.")
            return

        # Process the data
        college_list = []
        for item in data:
            college_info = {
                'college_id': item.get('college_id'),
                'college_name': item.get('college_name'),
                'location': item.get('location'),
                'affiliated_university': item.get('affiliated_university'),
                'course_offered': item.get('course_offered'),
                'specializations': item.get('specializations'),
                'course_duration': item.get('course_duration'),
                'fee_structure': item.get('fee_structure'),
                'scholarship_available': item.get('scholarship_available'),
                'eligibility_criteria': item.get('eligibility_criteria'),
                'distance_from_student': item.get('distance_from_student'),
                'student_satisfaction_rate': item.get('student_satisfaction_rate'),
                'placement_rate': item.get('placement_rate'),
                'hostel_available': item.get('hostel_available'),
                'campus_size': item.get('campus_size'),
                'mode_of_education': item.get('mode_of_education'),
                'nacc_rating': item.get('nacc_rating')
            }
            college_list.append(college_info)

        # Display the fetched data in the console
        print(pd.DataFrame(college_list))

        # Save the data to a CSV file in the current directory
        csv_path = os.path.join(os.getcwd(), 'synthetic_colleges_updated.csv')

        # Save the DataFrame to a CSV file (overwrite if exists)
        df = pd.DataFrame(college_list)
        df.to_csv(csv_path, index=False)

        print(f"Data successfully saved to {csv_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
fetch_data_from_mongo()
