# SOEN 345 Project

### Setting Up Script with Defects4j

Follow these steps to check out a fixed version of a project from Defects4J and prepare it for analysis:

1. Navigate to your Defects4J directory (that you have previously set up):

2. Create and navigate to a new directory for your specific project:
   ```
   mkdir project_name_checkout # name as you want
   cd project_name_checkout
   ```

3. Check out a fixed version of your project:
   ```
   # Replace PROJECT with your specific project and VERSION_NUMBER with the version number
   defects4j checkout -p PROJECT -v VERSION_NUMBERf -w ./
   ```
   
   For example:
   ```
   defects4j checkout -p Math -v 25f -w ./  # Math project, fixed version of bug #25
   ```

4. Generate the list of relevant classes of your project:
   ```
   defects4j export -p classes.relevant -o all_classes.txt
   ```

   - Verify that the all_classes.txt file exists in that directory before proceeding with the following steps to run the script.

5. Copy the script (script.py) from this repository and place it in your project directory:
   ```
   # Copy the script.py file from this repository into your project directory
   ```

6. Run the analysis script:
   ```
   python3 script.py # depends on your python version
   ```


