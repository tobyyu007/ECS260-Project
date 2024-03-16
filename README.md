# Correlation of Software Metrics and its Popularity

This study delves into the factors influencing the popularity of software projects on GitHub, focusing on JavaScript projects. It examines the impact of documentation, software quality, and developer diversity, employing a comprehensive analytical approach that includes data collection, filtering, and preprocessing from GitHub. The main findings of the study are as follows:

### Transparency and Governance Over Documentation:
We investigate the relationship between documentation, licensing, and project popularity. Contrary to existing assumptions, our analysis reveals that the presence of licensing and codes of conduct is more strongly correlated with popularity than documentation volume alone. This addresses the gap in previous research by emphasizing the crucial role of legal clarity and governance in fostering successful open-source communities.

### Balancing Software Quality and Complexity:
Our study explores the impact of software quality metrics on project popularity. By examining bug proneness, code cleanliness, and cognitive complexity, we bridge a gap in understanding how these factors influence project success. Our findings underscore the importance of maintaining clean code and managing cognitive complexity effectively to enhance project appeal and popularity.

### Embracing Diversity for Collaboration:
We investigate the effects of developer and programming language diversity on project popularity. This addresses a gap in the literature regarding the influence of diversity on project success. Our research highlights the positive impact of global contributor diversity while cautioning against excessive programming language diversity, providing valuable insights for fostering inclusive and successful open-source communities.

## Data structure
- `Analysis` folder: Contains scripts used for analyzing RQ1, RQ2, and RQ3.
- `Data` folder: Stores the data used for analysis.
- `EDA` folder: Retrieves data and performs data cleaning.
- `LDA` folder: Contains scripts used for performing Latent Dirichlet Allocation (LDA) analysis.
- `SonarQube` folder: Stores the main.py script that utilizes SonarQube to analyze a repository's Code Smell and Cognitive Complexity.

The PDF of this paper is provided in `report.pdf`.
