import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

#########################################################################################

def find_center(coordinates):
    '''
    Given a set of bbox coordinates ([x0, y0, x1, y1]), determine the center point
    of the rectangle made by the combination of those coordinates.
    (x0, y0), (x1, y0), (x0, y1), (x1, y1)
    '''
    center_point = [(coordinates[0] + coordinates[2])/2, 
                    (coordinates[1] + coordinates[3])/2]
    
    return center_point

#########################################################################################

def determine_distance(coordinate_1, coordinate_2):
    '''
    Given the coordinates of two points, determine the distance between them.
    '''    
    x0, y0 = coordinate_1
    x1, y1 = coordinate_2
    distance = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)

    return distance

#########################################################################################

def determine_point_overlap(point_coordinates, image_bbox, shift = 0):
    '''
    Given the coordinates of a point representing the center of a text bbox, determine
    if that point lays within the bounds of an image bbox.

    Optional shift variable to shift image bbox coordinates as many text centers are slightly
    outside of the image bbox.
    '''
    px, py = point_coordinates
    x0, y0, x1, y1 = image_bbox
    
    shift_magnitude = shift/100

    up = [px, py * (1 + shift_magnitude)]
    down = [px, py * (1 - shift_magnitude)]
    left = [px * (1 - shift_magnitude), py]
    right = [px * (1 + shift_magnitude), py]

    Overlap = False

    for direction in up, down, left, right:
        px, py = direction
        
        if x0 <= px <= x1 and y0 <= py <= y1:
            Overlap = True

    return Overlap

#########################################################################################

def create_image_list(current_page):
    '''
    Given a single page of a pdf document, isolate the image references on that page.
    '''
    image_list = current_page.get_images(full = True)
    img_refs = current_page.get_image_info(xrefs = True)
    img_refs = [i["xref"] for i in img_refs if i['has-mask'] == True]
    final_image_list = []

    if len(img_refs) > len(image_list):
        for ref in img_refs:
            for image in image_list:
                image_ref = image[0]

                if image_ref == ref:
                    final_image_list.append(image)

    if len(final_image_list) == 0:
        final_image_list = image_list
    
    image_rect = []
    image_center = []

    for image in final_image_list:
        current_rect = current_page.get_image_bbox(image)
        image_rect.append(current_rect)
        image_center.append(find_center([round(num) for num in current_rect]))
    
    return final_image_list, image_rect, image_center

#########################################################################################

def determine_rect_overlap(image_rect_list, image_list):
    '''
    Given a list of image rectangles and image references, determine the index of
    images which overlap. This occurs when an image is composed of a foreground and 
    background image superimposed on each other.
    '''
    Overlap_index = []

    for i in range(len(image_rect_list)):

        Index = i

        for j in range(len(image_rect_list)):
            if i != j:
                if determine_distance(find_center(image_rect_list[i]), find_center(image_rect_list[j])) < 10:
                    if image_list[i][1] == 0 or image_list[j][1] == 0:
                        index_pair = [min(i, j), max(i, j)]

                        Overlap_check = []

                        if len(Overlap_index) < 1:   
                            Index = index_pair
                        else:
                            for pair in Overlap_index:
                                Overlap_check.append(pair != index_pair)

                        if True in Overlap_check and False not in Overlap_check:
                            Index = index_pair

        Index_check = []

        if len(Overlap_index) > 1:
            for i in range(len(Overlap_index)):
                Current_numbers = Overlap_index[i]

                if isinstance(Current_numbers, list):
                    for i in range(len(Current_numbers)):
                        Index_check.append(Current_numbers[i])
                else:
                    Index_check.append(Current_numbers)

        if Index not in Index_check:
            Overlap_index.append(Index)

    return Overlap_index

#########################################################################################

def isolate_text(page, image_list):
    '''
    Given a single page from a pdf of pawns, isolate the text and text bbox center or each text box on that page.
    As the format of these input pdfs have two instances of each text box, loop through the text list and save the second
    instance of the text. As some text is written on two lines, combine the two lines together. In cases where a space is added
    at the end of the text box, remove the space.
    '''    
    blocks = page.get_text("dict", flags = 1)["blocks"] 
    text = []
    text_bbox = []
    text_bbox_center = []

    for block in blocks:  # iterate through the text blocks
        for lines in block["lines"]:  # iterate through the text lines
            for spans in lines["spans"]:  # iterate through the text spans
                if(spans["font"] == 'GoodOT-CondBold' or spans["font"] == 'DaxCondensed-Bold') and spans["text"] != 'BB':
                    text.append(spans["text"])
                    text_bbox.append(spans["bbox"])
                    text_bbox_center.append(find_center(spans["bbox"]))

    final_text = []
    final_text_bbox = []

    Flag = False

    for i in range(0, len(text)):

        current_text = text[i]
        current_bbox = text_bbox[i]
        current_center = text_bbox_center[i]

        if len(text) > len(image_list):
    
            if i % 2 == 0: 

                if Flag == True:
                    Flag = False

                else:

                    if i < len(text) - 2:
                        
                        current_center = find_center(current_bbox)
                        next_center = find_center(text_bbox[i + 2])
                        distance = determine_distance(current_center, next_center)
                    
                        if distance < 10:
                            current_text = current_text + text[i + 2]
                            
                            if current_text[-1] == ' ':
                                current_text = current_text[:-1]

                            final_text.append(current_text)
                            final_text_bbox.append([round(num) for num in current_bbox])
                            Flag = True

                        else:

                            if current_text[-1] == ' ':
                                current_text = current_text[:-1]

                            final_text.append(current_text)
                            final_text_bbox.append([round(num) for num in current_bbox])

                    else:

                        if current_text[-1] == ' ':
                                current_text = current_text[:-1]
                                
                        final_text.append(current_text)
                        final_text_bbox.append([round(num) for num in current_bbox])

        #################################################################################

        else:

            if i < len(text) - 2:
                        
                current_center = find_center(current_bbox)
                next_center = find_center(text_bbox[i + 2])
                distance = determine_distance(current_center, next_center)
            
                if distance < 10:
                    current_text = current_text + text[i + 2]
                    
                    if current_text[-1] == ' ':
                        current_text = current_text[:-1]

                    final_text.append(current_text)
                    final_text_bbox.append([round(num) for num in current_bbox])
                    Flag = True

                else:

                    if current_text[-1] == ' ':
                        current_text = current_text[:-1]

                    final_text.append(current_text)
                    final_text_bbox.append([round(num) for num in current_bbox])

            else:

                if current_text[-1] == ' ':
                        current_text = current_text[:-1]
                        
                final_text.append(current_text)
                final_text_bbox.append([round(num) for num in current_bbox])

    return final_text, final_text_bbox

#########################################################################################

def plot_image_and_text_shift(image_bbox_list, text_bbox_list, shift):
    '''
    Given a list of bbox bounds for images and text, graph a representation of the image bbox
    and place a point representing the center of the text bbox to determine how each text box
    relates to the related image. This is useful for determining why text boxes may be assigned 
    to multiple images or why text boxes are not assigned to any image.
    '''    
    # Create the figure and axes object
    fig, ax = plt.subplots()

    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 1000)

    # Loop through the image coordinates and add them to the plot
    for coordinates in image_bbox_list:
        x0, y0, x1, y1 = coordinates

        Rectangle = patches.Rectangle((x0, y0), 
                                      x1-x0, 
                                      y1-y0, 
                                      linewidth = 1, 
                                      edgecolor = 'b', 
                                      facecolor = 'none')

        ax.add_patch(Rectangle)

    for text in text_bbox_list:
        point = find_center(text)

        shift_magnitude = shift/100

        left = [point[0] * (1 - shift_magnitude), point[1]]
        right = [point[0] * (1 + shift_magnitude), point[1]]
        up = [point[0], point[1] * (1 + shift_magnitude)]
        down = [point[0], point[1] * (1 - shift_magnitude)]

        for direction in left, right, up, down:
            
            plt.plot(direction[0], direction[1], marker = 'o')

    return plt.show()