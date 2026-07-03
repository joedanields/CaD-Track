## **AI-Based Image Difference Detection, Visualization, and Automated Change Summarization** 

Comparing two versions of an image manually is time-consuming and prone to human error, especially when the differences are subtle or distributed across multiple regions. Automated image comparison systems are widely used in quality inspection, surveillance, document verification, construction monitoring, medical imaging, and version tracking. 

The objective of this project is to develop an intelligent application capable of identifying visual differences between two images, highlighting the changed regions, and generating a human-readable summary describing the detected changes. 

## **Objective** 

Design and implement an AI-powered image comparison system that accepts two input images, detects and localizes visual differences, produces an annotated visualization, and generates a natural language summary explaining the observed changes. 

## **Functional Requirements** 

## **FR-1 Image Upload** 

- The system shall allow the user to upload two images or PDF files containing static images. 

- Supported formats shall include JPG, JPEG, PNG, and PDF. 

- The system shall validate the uploaded files before processing. 

## **FR-2 Image Preprocessing** 

- Resize images to a common resolution if necessary. 

- Perform alignment or registration when images have slight positional differences. 

- Normalize image quality where required. 

## **FR-3 Difference Detection** 

The system shall: 

- Compare both images pixel-wise and/or using computer vision techniques. 

- Detect added, removed, or modified regions. 

- Ignore insignificant noise where possible. 

- Produce a difference mask identifying changed areas. 

## **FR-4 Difference Visualization** 

The system shall generate a visual output that includes: 

- Bounding boxes around changed regions. 

- Highlighted difference mask or heatmap. 

- Side-by-side comparison of the original images. 

- Optional overlay of detected changes. 

## **FR-5 Difference Statistics** 

The system shall compute: 

- Number of detected changed regions. 

- Percentage of image changed. 

- Area covered by changes. 

- Coordinates of detected regions (optional). 

## **FR-6 AI-Based Change Summary** 

The system shall automatically generate a concise paragraph describing the detected changes. 

The summary should include: 

- Overall comparison result. 

- Major changed objects or regions. 

- Approximate locations of changes (top, bottom, left, right, center). 

- Severity or extent of modifications. 

- Confidence level (optional). 

Example: 

"The comparison identified four significant changes between the two images. A new vehicle has appeared in the lower-right region, while an existing tree in the upper-left has been removed. Minor structural modifications were detected near the center of the image, affecting approximately 8.7% of the total image area." 

## **Expected Inputs** 

- Image A (Reference Image) 

- Image B (Comparison Image) 

## **Expected Outputs** 

1. Original Image A 

2. Original Image B 

3. Difference Visualization 

4. Highlighted Changed Regions 

5. Difference Statistics 

6. AI-Generated Summary Paragraph 

## **Deliverables** 

- Source code 

- Project documentation 

- Requirements document 

- System architecture diagram 

- Sample input and output images 

- Demonstration video (optional) 

- README with setup instructions 

## **Refer** : (MUST) 

https://arxiv.org/abs/2201.00625 https://arxiv.org/pdf/2505.01530 

## **Github for Reference:** 

https://github.com/javvi51/eDOCr https://github.com/Bakkopi/engineering-drawing-extractor - https://github.com/topics/cad drawings 

