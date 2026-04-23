# apply_ui.py
import os
import glob

def patch_all_pages():
    print("Initiating Global UI Update...")
    
    # Find all Python files in the pages directory
    page_files = glob.glob("pages/*.py")
    
    if not page_files:
        print("❌ Error: Could not find the 'pages' folder.")
        return

    for file_path in page_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Skip if already updated
        if "from shared_ui import render_top_bar" in content:
            print(f"⏩ Skipping {os.path.basename(file_path)} (Already updated)")
            continue
            
        print(f"🔧 Injecting Shared UI into {os.path.basename(file_path)}...")
        
        # 1. Inject the import statement at the top
        content = content.replace(
            "import streamlit as st", 
            "import streamlit as st\nfrom shared_ui import render_top_bar"
        )
        
        # 2. Inject the function call right after the page config
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if "st.set_page_config" in line:
                new_lines.append("t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS")
        
        new_content = '\n'.join(new_lines)
        
        # Write the updated code back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    print("\n✅ Success! All pages have been updated with the new UI Engine.")

if __name__ == "__main__":
    patch_all_pages()