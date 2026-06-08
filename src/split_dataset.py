import os
import shutil

SOURCE_DIR = "dataset/raw/asl_alphabet_train/asl_alphabet_train"
OUTPUT_DIR = "dataset/split"

TARGET_LABELS = ["A", "B", "C", "L", "O", "V", "W", "Y"]

TRAIN_SIZE = 0.70
VAL_SIZE = 0.15
TEST_SIZE = 0.15

# Ne asigurăm că pornim de la un folder curat
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)

for label in TARGET_LABELS:
    source_folder = os.path.join(SOURCE_DIR, label)

    images = [
        img for img in os.listdir(source_folder)
        if img.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    # --- REPARAREA GREȘELII DE DATA LEAKAGE ---
    # 1. Sortăm fișierele alfabetic/cronologic (A1, A2, A3...) ca să păstrăm ordinea cadrelor video
    images.sort()

    # 2. Calculăm manual indicii de tăiere (fără shuffle aleatoriu)
    total_images = len(images)
    train_end = int(total_images * TRAIN_SIZE)
    val_end = int(total_images * (TRAIN_SIZE + VAL_SIZE))

    # 3. Împărțim setul în blocuri compacte de timp
    train_files = images[:train_end]
    val_files = images[train_end:val_end]
    test_files = images[val_end:]
    # ------------------------------------------

    for split_name, file_list in [
        ("train", train_files),
        ("validation", val_files),
        ("test", test_files)
    ]:
        output_folder = os.path.join(OUTPUT_DIR, split_name, label)
        os.makedirs(output_folder, exist_ok=True)

        for file_name in file_list:
            src = os.path.join(source_folder, file_name)
            dst = os.path.join(output_folder, file_name)
            shutil.copy2(src, dst)

    print(f"{label}: train={len(train_files)}, validation={len(val_files)}, test={len(test_files)}")

print("Dataset split completed successfully (Sequential mode).")