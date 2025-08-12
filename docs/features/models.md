# Learning statement models

The learning statement models validation and conversion tools in Ralph empower you to work with an LRS and ensure the quality of xAPI statements.
These features not only enhance the integrity of your learning data but also facilitate integration and compliance with industry standards.

This section provides insights into the supported models, their conversion, and validation.

## Supported statements

Learning statement models encompass a wide array of xAPI statement types, ensuring comprehensive support for your e-learning data.

1. **xAPI statements models**:
    - [LMS](https://profiles.adlnet.gov/profile/c4e8732c-428a-4aa0-9585-91bebcdea91d)
    - [Video](https://profiles.adlnet.gov/profile/90b2c849-d744-4d0c-8bd0-403e7859a35b)
    - [Virtual classroom](https://profiles.adlnet.gov/profile/4719f43e-28ef-4108-b76a-5fbde91c6f68)

## Statements validation

In learning analytics, the validation of statements takes on significant importance. 
These statements, originating from diverse sources, systems or applications, must align with specific standards such as [xAPI](https://xapi.com/) for the best known. 
The validation process becomes essential in ensuring that these statements meet the required standards, facilitating data quality and reliability. 

Ralph allows you to automate the validation process in your production stack. 
xAPI statements are supported.

!!! warning 

    For now, validation is effective only with supported [learning statement models](#learning-statement-models) on Ralph. About xAPI statements, an [issue](https://github.com/openfun/ralph/issues/388) is open to extend validation to any xAPI statement.

Check out tutorials to test the validation feature:

- [`validate` with Ralph as a CLI](../tutorials/cli.md#validate-command)
- [`validate` with Ralph as a library](../tutorials/library.md#validate-method)
