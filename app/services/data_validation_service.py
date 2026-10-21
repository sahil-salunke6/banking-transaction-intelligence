
import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "amount",
    "merchant",
    "merchant_category",
    "status",
    "channel",
    "country",
    "transaction_time",
]


def validate_transaction_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate transaction records from a Pandas DataFrame.

    Returns:
        valid_df: Records that passed validation.
        rejected_df: Records that failed validation, with reasons.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a Pandas DataFrame.")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Work on a copy so the original DataFrame is unchanged.
    cleaned_df = df.copy()

    # Normalize text fields by removing surrounding whitespace.
    text_columns = [
        "transaction_id",
        "customer_id",
        "merchant",
        "merchant_category",
        "status",
        "channel",
        "country",
    ]

    for column in text_columns:
        cleaned_df[column] = (
            cleaned_df[column]
            .astype("string")
            .str.strip()
        )

    # Convert amounts to numbers.
    # Invalid values such as "abc" become NaN and are rejected.
    cleaned_df["amount"] = pd.to_numeric(
        cleaned_df["amount"],
        errors="coerce",
    )

    # Convert timestamps to datetime.
    # Invalid timestamps become NaT and are rejected.
    cleaned_df["transaction_time"] = pd.to_datetime(
        cleaned_df["transaction_time"],
        errors="coerce",
    )

    validation_errors = [[] for _ in range(len(cleaned_df))]

    def add_error(mask: pd.Series, message: str) -> None:
        for position, invalid in enumerate(mask.fillna(True).tolist()):
            if invalid:
                validation_errors[position].append(message)

    # Required text fields must not be missing or blank.
    for column in text_columns:
        invalid_text = (
            cleaned_df[column].isna()
            | cleaned_df[column].eq("").fillna(True)
        )
        add_error(
            invalid_text,
            f"{column} is required",
        )

    # Amount must be numeric, finite, and greater than zero.
    invalid_amount = (
        cleaned_df["amount"].isna()
        | ~cleaned_df["amount"].map(
            lambda value: (
                pd.notna(value)
                and value not in (float("inf"), float("-inf"))
            )
        )
        | cleaned_df["amount"].le(0)
    )

    add_error(
        invalid_amount,
        "amount must be a finite number greater than zero",
    )

    # Transaction timestamp must be valid.
    add_error(
        cleaned_df["transaction_time"].isna(),
        "transaction_time must be a valid timestamp",
    )

    has_errors = pd.Series(
        [bool(errors) for errors in validation_errors],
        index=cleaned_df.index,
    )

    valid_df = cleaned_df.loc[~has_errors].copy()

    rejected_df = cleaned_df.loc[has_errors].copy()
    rejected_positions = [
        position
        for position, errors in enumerate(validation_errors)
        if errors
    ]

    rejected_df["_validation_errors"] = [
        validation_errors[position]
        for position in rejected_positions
    ]

    return valid_df, rejected_df
