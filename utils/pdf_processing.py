import fitz  # PyMuPDF
import os

def extract_images_from_pdf(pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_count = 0

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        image_list = page.get_images(full=True)

        text_blocks = [
            block for block in page.get_text("dict")["blocks"]
            if "lines" in block
        ]

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_filename = f"Image{image_count + 1}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            caption_text = "No caption found"
            if image_count < len(text_blocks):
                block = text_blocks[image_count]
                caption_lines = [
                    span["text"]
                    for line in block["lines"]
                    for span in line["spans"]
                ]
                caption_text = " ".join(caption_lines).strip()

            caption_filename = f"Caption{image_count + 1}.txt"
            caption_path = os.path.join(output_folder, caption_filename)

            with open(caption_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(caption_text)

            image_count += 1

    return image_count
