@echo off
for /D %%u in (models\users\*) do (
    python models\train_user_habit_model.py %%~nxu
)
