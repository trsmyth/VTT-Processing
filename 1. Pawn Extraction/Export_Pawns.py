import fitz
import numpy as np
import cv2
from Export_Functions import plot_image_and_text_shift
from Export_Functions import isolate_text, find_center
from Export_Functions import determine_rect_overlap, determine_distance, create_image_list

file = ['C:/Users/Timot/Desktop/Paizo_Products/Assets/Pawn_Packs/Beginner_Box.pdf', 
        'C:/Users/Timot/Desktop/Paizo_Products/Assets/Pawn_Packs/Fist_of_the_Ruby_Phoenix.pdf', 
        'C:/Users/Timot/Desktop/Paizo_Products/Assets/Pawn_Packs/NPC_Pawns.pdf', 
        'C:/Users/Timot/Desktop/Paizo_Products/Assets/Pawn_Packs/Player_Pawns.pdf', 
        'C:/Users/Timot/Desktop/Paizo_Products/Assets/Pawn_Packs/Traps_and_Treasures_Pawns.pdf']

output_folder = ['C:/Users/Timot/Desktop/Paizo_Products/Pawns/Beginner Box', 
                 'C:/Users/Timot/Desktop/Paizo_Products/Pawns/Fist of the Ruby Phoenix', 
                 'C:/Users/Timot/Desktop/Paizo_Products/Pawns/NPC Pawns', 
                 'C:/Users/Timot/Desktop/Paizo_Products/Pawns/Player Pawns', 
                 'C:/Users/Timot/Desktop/Paizo_Products/Pawns/Traps and Treasures']

# List the number of pages at the beginning and end of the pdf which do not
# contain images to be extracted. I.e. title page and TOC
Pages = [[0, 0], 
         [1, 2], 
         [2, 1], 
         [1, 2],
         [1, 2]]

'''
Specify the value to shift text up, down, left, and right. Text frequently lies 
outside of the image bbox despite appearing inside when viewed through a pdf viewer.
Remove comment for plot_image_and_text_shift function below to see where text box centers
actually appear on the pdf, and if the specified shift is appropriate for the needed pdf.
Shift of 3 appears to work for a wide range of paizo pawn pdfs.
'''
shift = 3
plot = False

# For each file listed above in 'file' list
for single_file_index in range(len(file)):

    # Open the pdf document
    pdf_document = fitz.open(file[single_file_index])

    # Define the number of title pages and back pages in the pdf
    # according to the 'Pages' list specified above
    Title_Pages = Pages[single_file_index][0]
    Back_Pages = Pages[single_file_index][1]

    # Determine the number of pages with images present within the specified document
    page_count = range(0 + Title_Pages, pdf_document.page_count - Back_Pages)

    ######################################################################

    # For each page in the current document
    for page_index in page_count:
        
        # Specify the current page
        page = pdf_document[page_index]

        # Create a list of images, image rectangles, and the center point
        # of each image found on the page
        image_list, image_rect, image_center = create_image_list(page)

        # Turn the image rectangle list into an actual list for further use
        image_rect = [list(rect[0:4]) for rect in image_rect]
            
        ################

        '''
        Determine the index of overlaps between image rectangles and images on the list.
        This is for situations when an image is composed of two or more superimposed images
        allowing for a foreground and background image.
        '''
        Overlap_index = determine_rect_overlap(image_rect, image_list)
                            
        all_first_position = [] # First position
        overlap_first_position = [] # First position if overlap found
        multiple_positions = [] # First or other position of images which have an overlap

        '''
        Determine the index of images which appear once or in the first position
        if images overlap. Also determine the index of images not in first position
        as well as all images which overlap.
        '''
        for Index in Overlap_index:
            Flattened_overlap = []

            # Overlapping image indices are lists
            if isinstance(Index, list):
                multiple_positions.append(Index)
                Flattened_overlap.append(Index[0])
                overlap_first_position.append(Index[0])

            else:
                Flattened_overlap.append(Index)

            all_first_position.append(Flattened_overlap)

        # Flatten lists so lists are lists and not nested lists
        all_first_position = [num for sublist in all_first_position for num in sublist]
        multiple_positions_flat = [num for sublist in multiple_positions for num in sublist]

        ################

        # Isolate the image name and bbox of text box
        Label, Text_bbox = isolate_text(page, image_rect)

        # Optional plot image bboxes and shift text to show where text and images overlap.
        # This is particularly useful for testing new pawn packs
        if plot == True:
            plot_image_and_text_shift(image_rect, Text_bbox, shift = shift)

        ################

        Arranged_image_title = []

        # For each image index represening an image in the first position,
        # determine which text bbox overlaps with the image. 
        for index in all_first_position:
            rect = image_rect[index] # Isolate image rect of current index

            Distances = []
            for bbox in Text_bbox: # for each text bbox
                # Determine the distance between the current image rect and each text bbox
                Distances.append(determine_distance(find_center(rect), find_center(bbox)))

            # Find the minimum distance between the center of an image rect and a text bbox
            min_distance_index = Distances.index(min(Distances))
            Arranged_image_title.append([Label[min_distance_index]])

        # Flatten list so list is list and not nested list
        Arranged_image_title = [name for sublist in Arranged_image_title for name in sublist]

        ################

        # Loop through every image on the image list
        for i in range(len(image_list)):

            # If i is a first position image, meaning it is an image and has a corresponding name
            if i in all_first_position:

                # Isolate the index position of the image and define the current image name
                index = all_first_position.index(i)
                current_image_name = f"{Arranged_image_title[index]}"

            # If image i is not part of a multi-image image
            if i not in multiple_positions_flat:

                # Isolate the current image and determine the image extension
                image = image_list[i]
                image_ext = pdf_document.extract_image(image[0])["ext"]

                # Define the pixmap of the current image
                img = fitz.Pixmap(pdf_document.extract_image(image[0])["image"])

                # If image position 1 is > 0, a mask is present and is incorporated in the final pixmap
                if image[1] > 0:
                    mask = fitz.Pixmap(pdf_document.extract_image(image[1])["image"])
                    pix = fitz.Pixmap(img, mask)
                
                else:
                    pix = fitz.Pixmap(img)

                # Try to create a 4d numpy array from the pixmap. If the dimmensions do not allow for that,
                # keep the image defined as image
                try:
                    image = np.frombuffer(buffer = pix.samples, dtype = np.uint8).reshape((pix.height, pix.width, 4))
                
                except:
                    image = image
                    
                # Define image dimmensions
                h, w, _ = image.shape
                    
                # Convert the image to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                ##########################################

                '''
                This section is used to remove white or black backgrounds of images if they are present.
                Threshold values of 245 and 15 are employed for white and black, respectively but these
                values may need to be changed based on the specific artwork used in a specific pawn pack.
                These values work with all images in tested pawn packs, but future packs may require tuning.
                To do so, check the min/max values of gray[0] and adjust if necessary.
                '''
                # If the maximum value of the first dimmenstion of the array is white (255)
                # There is a white background which we will want to remove and replace with transparency
                if max(gray[0]) == 255:
                    thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)[1] # Threshold with 245 limit
                    gray = 255 - gray # invert gray image
                    thresh = 255 - thresh # invert thresh
                
                # If not, the background is black and should be removed and replaced with transparency
                else:
                    thresh = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)[1] # Threshold with 15 limit

                ##########################################

                pixels = cv2.countNonZero(thresh) # Count the number of pixels which have color (not zero)
                ratio = (pixels/(h * w)) * 100 # Determine ratio of pixels with color
                
                if ratio > 75:

                    # If ratio > 75, no background is present and the image can be saved normally
                    with open(f'{output_folder[single_file_index]}/{current_image_name}.png', "wb") as image_file:
                        image_file.write(pix.tobytes())
                        print(f"[+] Image saved as {current_image_name}.")

                else:

                    # Create a mask by eroding the threshold image and morph_close
                    kernel = np.ones((3, 3), np.uint8)
                    mask = cv2.erode(thresh, kernel, iterations = 1)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

                    # Create a new RGBA image from the current image
                    new_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
                    new_img[:, :, 3] = mask # Apply the transparency mask
                    new_img[np.where(np.all(new_img == 255, -1))] = 0 # Set transparency of fully white pixels to 0
                    new_img[np.where(np.all(new_img == 0, -1))] = 0 # Set transparency of fully black pixels to 0

                    # Save the new image with transparency mask as a png without compression
                    cv2.imwrite(f'{output_folder[single_file_index]}/{current_image_name}.png', new_img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                    print(f"[+] Image saved as {current_image_name}.")

            # If i is in the first position of an overlap of images
            elif i in overlap_first_position:
                
                # Define index of the overlap position
                index = overlap_first_position.index(i)

                # Define the first and second image in the overlap
                image1 = multiple_positions[index][0]
                image2 = multiple_positions[index][1]

                # If a mask is not present in image1, the top image is image2
                if image_list[image1][1] == 0:
                    top_image = image_list[image2]
                    bottom_image = image_list[image1]

                # If a mask is not present in image2, the top image is image1
                else:
                    if image_list[image2][1] == 0:
                        top_image = image_list[image1]
                        bottom_image = image_list[image2]

                # Determine the image extension
                image_ext = pdf_document.extract_image(top_image[0])["ext"]

                # Create the top image pixmap
                top_image_image = fitz.Pixmap(pdf_document.extract_image(top_image[0])["image"])
                top_image_mask = fitz.Pixmap(pdf_document.extract_image(top_image[1])["image"])
                top_image_pix = fitz.Pixmap(top_image_image, top_image_mask)

                # Create the bottom image pixmap
                bottom_image_pix = fitz.Pixmap(pdf_document.extract_image(bottom_image[0])["image"])

                # Define the height and width of a new combined image based on the maximum dimmensions of both images
                new_width = max(bottom_image_pix.width, top_image_pix.width)
                new_height = max(bottom_image_pix.height, top_image_pix.height)

                # Create an image rectangle of indicated size
                image_rect = fitz.Rect(0, 0, new_width, new_height)
                
                # Open a new blank document of indicated dimmensions.
                # Add the foreground and background image, overlaying the top image over the bottom image.
                doc = fitz.open()
                storage_page = doc.new_page(width = new_width, height = new_height)
                storage_page.insert_image(image_rect, stream = bottom_image_pix.tobytes(), overlay = False)
                storage_page.insert_image(image_rect, stream = top_image_pix.tobytes(), overlay = True)

                # Get the pixmap of the combined image
                pix = storage_page.get_pixmap()

                # Save the combined image
                with open(f'{output_folder[single_file_index]}/{current_image_name}.png', "wb") as image_file:
                    image_file.write(pix.tobytes())
                    print(f"[+] Image saved as {current_image_name}.")