#!/bin/bash

# Define log file
LOG_FILE="eval.log"
echo "" > $LOG_FILE  # Clear previous logfile contents

# Step 1: Run run_5.py
echo "Running run_5.py..." | tee -a $LOG_FILE
if python run_5.py; then
    echo "Step 1: run_5.py completed successfully." >> $LOG_FILE
else
    echo "Step 1: run_5.py failed." >> $LOG_FILE
    exit 1
fi

# Step 2: Move log files for run_5.py
echo "Moving log files from run_5.py..." | tee -a $LOG_FILE
if mv 17*.log snapshots/run.log; then
    echo "Step 2: Log files moved successfully." >> $LOG_FILE
else
    echo "Step 2: Log file move operation failed." >> $LOG_FILE
    exit 1
fi

# Step 3: Create warehouse_5b.zip
echo "Creating warehouse_5b.zip..." | tee -a $LOG_FILE
if zip -r warehouse_5b.zip . >> $LOG_FILE; then
    echo "Step 3: warehouse_5b.zip created successfully." >> $LOG_FILE
else
    echo "Step 3: Failed to create warehouse_5b.zip." >> $LOG_FILE
    exit 1
fi

# Step 4: Move snapshots folder to snapshots_2
echo "Renaming snapshots folder to snapshots_2..." | tee -a $LOG_FILE
if mv snapshots snapshots_2; then
    echo "Step 4: snapshots folder renamed to snapshots_2 successfully." >> $LOG_FILE
else
    echo "Step 4: Failed to rename snapshots folder to snapshots_2." >> $LOG_FILE
    exit 1
fi

# Step 5: Run run_6.py
echo "Running run_6.py..." | tee -a $LOG_FILE
if python run_6.py; then
    echo "Step 5: run_6.py completed successfully." >> $LOG_FILE
else
    echo "Step 5: run_6.py failed." >> $LOG_FILE
    exit 1
fi

# Step 6: Move log files for run_6.py
echo "Moving log files from run_6.py..." | tee -a $LOG_FILE
if mv 17*.log snapshots/run.log; then
    echo "Step 6: Log files moved successfully." >> $LOG_FILE
else
    echo "Step 6: Log file move operation failed." >> $LOG_FILE
    exit 1
fi

# Step 7: Create warehouse_6b.zip
echo "Creating warehouse_6b.zip..." | tee -a $LOG_FILE
if zip -r warehouse_6b.zip . >> $LOG_FILE; then
    echo "Step 7: warehouse_6b.zip created successfully." >> $LOG_FILE
else
    echo "Step 7: Failed to create warehouse_6b.zip." >> $LOG_FILE
    exit 1
fi

echo "All steps completed successfully!" >> $LOG_FILE
exit 0