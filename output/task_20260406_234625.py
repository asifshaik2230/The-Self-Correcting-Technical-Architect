import time
import threading
from typing import Union

class TokenBucket:
    """
    Implements a robust Token Bucket rate limiting algorithm.

    This class manages a bucket of tokens that are refilled at a constant rate.
    Requests consume tokens, and if not enough tokens are available, the request
    is rejected. The bucket's token count never exceeds its maximum capacity.

    The implementation is thread-safe, allowing it to be used in concurrent
    environments without race conditions.
    """

    # Type hints for instance attributes
    _lock: threading.Lock
    capacity: float
    refill_rate: float
    tokens: float
    last_refill_timestamp: float

    def __init__(self, capacity: float, refill_rate: float) -> None:
        """
        Initializes the TokenBucket with a specified capacity and refill rate.

        The bucket starts full, ready to process requests immediately.

        Args:
            capacity (float): The maximum number of tokens the bucket can hold.
                              Must be a positive number.
            refill_rate (float): The rate at which tokens are added to the bucket
                                 per second. Must be a positive number.

        Raises:
            ValueError: If capacity or refill_rate is not a positive number.
        """
        # Validate input parameters to ensure they are positive and numeric.
        if not isinstance(capacity, (int, float)) or capacity <= 0:
            raise ValueError("Capacity must be a positive number.")
        if not isinstance(refill_rate, (int, float)) or refill_rate <= 0:
            raise ValueError("Refill rate must be a positive number.")

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        
        # Initialize the bucket with its full capacity of tokens.
        self.tokens = self.capacity
        
        # Record the current time as the last refill timestamp.
        # This is crucial for calculating elapsed time for future refills.
        self.last_refill_timestamp = time.time()
        
        # Initialize a threading.Lock to ensure thread-safe access to the
        # bucket's state (tokens and last_refill_timestamp) in concurrent environments.
        self._lock = threading.Lock()

    def _refill_tokens(self) -> None:
        """
        Refills the tokens in the bucket based on the elapsed time since the
        last token update.

        This private helper method calculates how many tokens should have been
        added based on the `refill_rate` and the time elapsed since
        `last_refill_timestamp`. It updates the `tokens` count, ensuring it
        never exceeds the `capacity`. It also updates `last_refill_timestamp`
        to the current time.

        This method should only be called from within a locked context to
        ensure thread safety.
        """
        current_time = time.time()
        elapsed_time = current_time - self.last_refill_timestamp
        
        # Calculate the number of tokens that should have been added during
        # the elapsed time.
        tokens_to_add = elapsed_time * self.refill_rate
        
        # Add the calculated tokens to the current count, but ensure the total
        # does not exceed the bucket's maximum capacity.
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        
        # Update the last refill timestamp to the current time, marking this
        # moment as the last state update.
        self.last_refill_timestamp = current_time

    def allow_request(self, tokens: float = 1.0) -> bool:
        """
        Attempts to consume a specified number of tokens for a request.

        First, the bucket is refilled based on the elapsed time. Then, if
        enough tokens are available, they are consumed, and the method returns
        True, indicating the request is allowed. If there are not enough
        tokens, the request is rejected, and the method returns False,
        without consuming any tokens.

        Args:
            tokens (float): The number of tokens required for the request.
                            Defaults to 1.0. Must be a positive number.

        Returns:
            bool: True if the request is allowed and tokens are consumed,
                  False otherwise.

        Raises:
            ValueError: If the requested 'tokens' amount is not a positive number.
        """
        # Validate the requested tokens amount.
        if not isinstance(tokens, (int, float)) or tokens <= 0:
            raise ValueError("Tokens requested must be a positive number.")

        # Acquire the lock to protect the bucket's state during the operation.
        # The 'with' statement ensures the lock is automatically released
        # when exiting the block, even if exceptions occur.
        with self._lock:
            # Step 1: Refill the tokens in the bucket based on elapsed time.
            self._refill_tokens()

            # Step 2: Check if there are sufficient tokens for the current request.
            if self.tokens >= tokens:
                # If yes, consume the requested tokens.
                self.tokens -= tokens
                return True  # Request allowed.
            else:
                # If no, the request is rejected. Tokens are not consumed.
                return False # Request rejected.