@echo off
setlocal enabledelayedexpansion
echo Starting Automated Weekly Training Cycle...

:: Loop through all pickle files in the tokens directory
for %%f in (tokens\token_*.pickle) do (
    set "filename=%%~nf"
    :: Extract the email from the filename (e.g., token_user@gmail.com -> user@gmail.com)
    set "userid=!filename:token_=!"
    echo Training model for user: !userid!
    python models/train_user_habit_model.py --user_id !userid!
)

echo ✅ All User Models Updated Successfully.