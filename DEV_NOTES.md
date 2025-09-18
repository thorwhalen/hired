# hired

Streamline the job application process for job seekers

## Overview

The `hired` project is a Python package designed to streamline the job application process for job seekers. It uses a modern, engineering-driven approach, powered by AI agents, to help users customize their application materials, with a primary focus on resumes.

Unlike a comprehensive curriculum vitae (CV), a resume should be concise, ideally fitting on a single page. This requires careful selection of relevant work experiences, projects, and publications from a candidate's full professional history. The `hired` package leverages AI models to automate this traditionally manual and difficult process.

The core functionality of `hired` revolves around two main phases:

1.  **Content Generation**: An AI agent analyzes a candidate's full profile and a target job description to extract and distill the most relevant information. This information is then used to produce a structured content specification for the resume.
2.  **Rendering**: This structured content is then used to render the resume in various formats and styles. The rendering process is fully customizable, allowing a user to specify the output format (e.g., PDF, HTML, LaTeX) and a detailed rendering configuration (e.g., fonts, layouts, styles). To minimize boilerplate, the package will provide a system of conventions and templates for smart defaults.

The central component that connects these two phases is the **JSON Resume schema**, which serves as our standardized data middleware.

The final code will look something like this:

    from hired import mk_content_for_resume, mk_resume

    content = mk_content_for_resume(candidate_info_src, job_info_src)
    pdf_path = mk_resume(
        content,
        rendering
    )

## Project Components & Resources

### 1. The Data Standard: JSON Resume

The foundation of the `hired` package is the [JSON Resume schema](https://jsonresume.org/schema/). This open-source standard provides a well-defined structure for resume content, ensuring that your data is machine-readable and portable.

Key sections of the schema to focus on include:
* `basics`: Personal and contact information.
* `work`: An array of objects for work experience.
* `education`: An array of objects for academic history.
* `projects`: A list of projects with descriptions and highlights.
* `skills`: Categorized lists of skills and keywords.

### 2. The Rendering Engine & Pipeline

The rendering process will be separate from the content generation, allowing for a high degree of customization. There is no single standard for resume rendering; instead, rendering is handled by **themes**, which are a combination of a template and a stylesheet.

The main rendering pipeline will involve:
1.  **Templating**: Using a Python templating engine like [Jinja2](https://pypi.org/project/Jinja2/). This library will take the structured JSON data and populate a template (e.g., an HTML or LaTeX file) with the resume content.
2.  **Rendering**: The templated file is then converted into the final output format.
    * **PDF**: For generating professional PDF documents from HTML and CSS, [WeasyPrint](https://pypi.org/project/WeasyPrint/) is an excellent choice. It provides precise control over layout and typography.
    * **LaTeX**: To produce high-quality, typeset documents, you can use packages like [RenderCV](https://github.com/nelson-gomes/rendercv) or [cvcreator](https://pypi.org/project/cvcreator/). These tools use LaTeX as their backend for a more polished look.
    * **Word (.docx)**: For specific needs, packages like `jsonresume-docx` can be used to generate Word documents from the JSON data.

### 3. Python Packages & Tools

* **For Content Validation**: Ensure the input JSON data adheres to the schema.
    * [Pydantic](https://pypi.org/project/pydantic/): Define Python classes that match the JSON schema for robust validation.
    * [`jsonschema`](https://pypi.org/project/jsonschema/): A direct library for validating JSON files against a schema.
* **For Resume Generation**:
    * [Jinja2](https://pypi.org/project/Jinja2/): For rendering templates.
    * [WeasyPrint](https://pypi.org/project/WeasyPrint/): For HTML-to-PDF conversion.
    * [RenderCV](https://github.com/nelson-gomes/rendercv): A Python tool for LaTeX-based resume generation.
* **For Inspiration**: The [JSON Resume themes](https://jsonresume.org/themes/) provide many examples of how a single JSON file can be rendered in countless different styles.

### 4. References

* [JSON Resume Schema](https://jsonresume.org/schema/)
* [Python Tutorial: Generate a Web Portfolio and Resume from One JSON File](https://www.youtube.com/watch?v=ECt0TAl41Zk)
* [Jinja2](https://pypi.org/project/Jinja2/)
* [WeasyPrint](https://pypi.org/project/WeasyPrint/)
* [ReportLab](https://www.reportlab.com/)
* [Fpdf2](https://pypi.org/project/fpdf2/)
* [Pydantic](https://pypi.org/project/pydantic/)
* [`jsonschema`](https://pypi.org/project/jsonschema/)
* [RenderCV](https://github.com/nelson-gomes/rendercv)
* [cvcreator](https://pypi.org/project/cvcreator/)
* [JSON Resume Themes](https://jsonresume.org/themes/)

