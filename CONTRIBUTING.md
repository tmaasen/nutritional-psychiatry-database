# Contributing to the Nutritional Psychiatry Database

Thank you for your interest in contributing to the Nutritional Psychiatry Database! This project aims to create a comprehensive open-source database connecting food nutrients to mental health impacts. Your contributions will help advance the field of nutritional psychiatry and support applications promoting mental wellness through nutrition.

## How to Contribute

There are many ways to contribute to this project:

### 1. Scientific Contributions

If you have expertise in nutrition, neuroscience, or mental health:

- **Literature Reviews**: Help identify and summarize research on food-mood connections
- **Data Validation**: Review AI-generated predictions for scientific accuracy
- **Methodology Feedback**: Suggest improvements to our data collection and enrichment methods
- **Expert Annotations**: Provide expert annotations for foods in your area of expertise

### 2. Technical Contributions

If you have technical skills:

- **Code Contributions**: Improve our data processing pipelines or AI enrichment scripts
- **Data Visualization**: Create visualizations to help understand the database
- **API Development**: Help build APIs for accessing the database
- **Documentation**: Improve technical documentation and examples

### 3. Database Expansion

- **New Food Entries**: Contribute data for foods not yet in the database
- **Additional Nutrients**: Add data for new brain-specific nutrients
- **Bioactive Compounds**: Contribute data on bioactive compounds
- **Mental Health Impacts**: Add evidence-based mental health impacts with citations

## Contribution Guidelines

### Quality Standards

All contributions should uphold these standards:

1. **Scientific Rigor**: All data must be backed by scientific evidence when possible
2. **Transparency**: Clear source attribution and confidence ratings
3. **Completeness**: Follow the established schema with all required fields
4. **Documentation**: Include clear documentation for all contributions

### Code Contributions

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

Please ensure your code:
- Follows our existing style and conventions
- Includes appropriate documentation
- Passes all existing tests
- Includes new tests for new functionality

### Data Contributions

When contributing data:

1. Follow the established schema format
2. Include source citations for all data points
3. Add confidence ratings based on the quality of source data
4. Document your methodology for derived or calculated values
5. Submit via pull request with clear documentation

### AI-Generated Contributions

For AI-generated contributions:

1. Clearly mark the data as AI-generated
2. Document the prompt and model used
3. Include confidence scoring
4. Where possible, validate against literature sources
5. Be transparent about limitations and assumptions

## Getting Started

### Setup Development Environment

```bash
# Clone your fork of the repository
git clone https://github.com/your-username/nutritional-psychiatry-database.git
cd nutritional-psychiatry-database

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export USDA_API_KEY=your_api_key
export OPENAI_API_KEY=your_openai_key  # Only needed for AI enrichment
```

### Project Structure

Familiarize yourself with the project structure:

```
nutritional-psychiatry-database/
├── README.md                       # Project overview
├── LICENSE                         # MIT license
├── CONTRIBUTING.md                 # This file
├── schema/                         # Schema definitions
├── scripts/                        # Data processing scripts
│   ├── data_collection/           
│   ├── data_processing/            
│   └── ai/                         
├── data/                           # The database
│   ├── raw/                       
│   ├── processed/                  
│   └── enriched/                   
└── docs/                           # Documentation
```

## Contribution Review Process

All contributions will go through a review process:

1. **Initial Review**: Basic checks for adherence to guidelines
2. **Technical Review**: For code contributions
3. **Scientific Review**: For data and methodology contributions
4. **Revision**: Addressing reviewer feedback
5. **Acceptance**: Merging into the main database

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

## Communication

- **GitHub Issues**: For bug reports, feature requests, and discussions
- **Pull Requests**: For submitting contributions
- **Email**: For private communications with maintainers

## Recognition

All contributors will be recognized in the project documentation. Significant contributions may be highlighted in publications or presentations about the database.

## Questions?

If you have any questions about contributing, please open an issue or contact the project maintainers directly.

Thank you for contributing to advancing the field of nutritional psychiatry!
