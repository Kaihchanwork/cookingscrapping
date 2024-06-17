import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Function to convert time string to total seconds (e.g., '1.11.47' -> 1*60 + 11.47 seconds)
def time_to_seconds(time_str):
    try:
        if '.' in time_str:
            parts = time_str.split('.')
            if len(parts) == 3:
                minutes = int(parts[0])
                seconds = int(parts[1])
                milliseconds = int(parts[2])
                return minutes * 60 + seconds + milliseconds / 100
        return np.nan
    except ValueError:
        return np.nan

# Load the new data
data = pd.read_csv('race_records_20240616.csv')

# Debug: Print the first few rows of the dataset
print("Initial data:")
print(data.head())

# Check for unique values in the 'Finish Time' column
print("Unique values in 'Finish Time' before conversion:")
print(data['Finish Time'].unique())

# Convert 'Finish Time' to seconds
data['Finish Time'] = data['Finish Time'].apply(time_to_seconds)

# Convert 'Distance' to numeric
data['Distance'] = pd.to_numeric(data['Distance'], errors='coerce')

# Debug: Print the first few rows of the dataset after conversion
print("Data after converting 'Finish Time' to seconds:")
print(data.head())

# Clean the data
# Identify numerical columns
numerical_features = ['Draw', 'Rating', 'Win Odds', 'Actual Weight', 'Declared Horse Weight']
extra_numerical_features = [col for col in data.columns if col.startswith(('B', 'BO', 'CC', 'CP', 'CO', 'E', 'H', 'P', 'PC', 'PS', 'SB', 'SR', 'TT', 'V', 'VO', 'XB'))]
# Exclude 'Horse Number' and 'Horse Name' explicitly
extra_numerical_features = [col for col in extra_numerical_features if col not in ['Horse Number', 'Horse Name']]
all_numerical_features = numerical_features + extra_numerical_features

# Convert only numerical columns to numeric and coerce errors to NaN
data[all_numerical_features] = data[all_numerical_features].apply(pd.to_numeric, errors='coerce')

# Fill NaN values with 0 for boolean features before converting to int
for col in extra_numerical_features:
    data[col] = data[col].fillna(0).astype(int)

# Debug: Print the first few rows of the dataset after filling NaNs
print("Data after filling NaNs in extra numerical features:")
print(data.head())

# Drop rows with NaN values in 'Finish Time'
data.dropna(subset=['Finish Time'], inplace=True)

# Debug: Print the number of rows after dropping NaNs in 'Finish Time'
print(f"Number of rows after dropping NaNs in 'Finish Time': {len(data)}")

# Convert categorical features to numerical values
categorical_features = ['Horse Number', 'Horse Name', 'Racecourse', 'Track', 'Course', 'Distance', 'Going', 'Race Class', 'Trainer', 'Jockey']

# Function to train model based on specific distance
def train_model_for_distance(data, distance):
    # Ensure distance is numeric
    distance = float(distance)

    # Filter the data for the given distance
    filtered_data = data[data['Distance'] == distance]

    if filtered_data.empty:
        raise ValueError(f"No data available for distance {distance}")

    # Define features and target variable
    X = filtered_data[categorical_features + all_numerical_features]
    y = filtered_data['Finish Time']

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Column transformer for preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='mean')),
                ('scaler', StandardScaler())
            ]), all_numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Define the model pipeline
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(random_state=42))
    ])

    # Hyperparameter tuning
    param_grid = {
        'regressor__n_estimators': [100, 200],
        'regressor__max_depth': [None, 10, 20],
        'regressor__min_samples_split': [2, 5],
        'regressor__min_samples_leaf': [1, 2]
    }
    
    grid_search = GridSearchCV(model, param_grid, cv=3, scoring='neg_mean_squared_error', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    
    # Best model
    best_model = grid_search.best_estimator_

    # Make predictions
    y_pred = best_model.predict(X_test)

    # Evaluate the model
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Define an acceptable error threshold (e.g., 5 seconds)
    error_threshold = 1.0
    accuracy = np.mean(np.abs(y_test - y_pred) <= error_threshold)
    
    print(f'Mean Absolute Error: {mae}')
    print(f'Mean Squared Error: {mse}')
    print(f'R^2 Score: {r2}')
    print(f'Accuracy within {error_threshold} seconds: {accuracy * 100:.2f}%')

    return best_model

# Function to predict finish time for new data
def predict_finish_time(horse_number, horse_name, racecourse, track, course, distance, going, race_class, draw, rating, trainer, jockey, win_odds, actual_weight, declared_horse_weight, **kwargs):
    # Train the model for the specific distance
    best_model = train_model_for_distance(data, distance)
    
    new_data = pd.DataFrame({
        'Horse Number': [horse_number],
        'Horse Name': [horse_name],
        'Racecourse': [racecourse],
        'Track': [track],
        'Course': [course],
        'Distance': [distance],
        'Going': [going],
        'Race Class': [race_class],
        'Draw': [draw],
        'Rating': [rating],
        'Trainer': [trainer],
        'Jockey': [jockey],
        'Win Odds': [win_odds],
        'Actual Weight': [actual_weight],
        'Declared Horse Weight': [declared_horse_weight],
        **kwargs
    })
    
    # Add missing columns with default values
    for col in extra_numerical_features:
        if col not in new_data:
            new_data[col] = 0
    
    # Convert boolean features to integers (1 for True, 0 for False)
    for col in extra_numerical_features:
        new_data[col] = new_data[col].astype(int)
    
    # Apply the same preprocessing steps to the new data
    new_data_preprocessed = best_model.named_steps['preprocessor'].transform(new_data)
    
    # Make prediction
    finish_time_pred = best_model.named_steps['regressor'].predict(new_data_preprocessed)
    
    return finish_time_pred[0]

# Example usage of the prediction function
horse_number = 'HK_2022_H311'
horse_name = 'GLORY ELITE'
racecourse = 'ST'
track = 'Turf'
course = 'C+3'
distance = 1200
going = 'S'
race_class = '4'
draw = 2
rating = 60
trainer = 'TKH'
jockey = 'LDE'
win_odds = 1.6
actual_weight = 135
declared_horse_weight = 1189
extra_features = {
    'B': False, 'B1': False, 'B2': False, 'B-': False, 'BO': False, 'BO1': False, 'BO2': False, 'BO-': False, 'CC': False, 'CC1': False, 'CC2': False, 'CC-': False,
    'CP': False, 'CP1': False, 'CP2': False, 'CP-': False, 'CO': False, 'CO1': False, 'CO2': False, 'CO-': False, 'E': False, 'E1': False, 'E2': False, 'E-': False,
    'H': True, 'H1': False, 'H2': False, 'H-': False, 'P': False, 'P1': False, 'P2': False, 'P-': False, 'PC': False, 'PC1': False, 'PC2': False, 'PC-': False,
    'PS': False, 'PS1': False, 'PS2': False, 'PS-': False, 'SB': False, 'SB1': False, 'SB2': False, 'SB-': False, 'SR': False, 'SR1': False, 'SR2': False, 'SR-': False,
    'TT': False, 'TT1': False, 'TT2': False, 'TT-': False, 'V': False, 'V1': False, 'V2': False, 'V-': False, 'VO': False, 'VO1': False, 'VO2': False, 'VO-': False,
    'XB': False, 'XB1': False, 'XB2': False, 'XB-': False
}

# Convert boolean extra_features to int
extra_features = {k: int(v) for k, v in extra_features.items()}

# Combine extra features with new data
predicted_time = predict_finish_time(horse_number, horse_name, racecourse, track, course, distance, going, race_class, draw, rating, trainer, jockey, win_odds, actual_weight, declared_horse_weight, **extra_features)
print(f'Predicted Finish Time: {predicted_time} seconds')
