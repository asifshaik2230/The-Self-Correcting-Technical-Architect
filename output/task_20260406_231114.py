import time
from typing import Union

class TokenBucket:
    """
    A class to implement the Token Bucket rate limiting algorithm.
    
    Attributes:
        capacity (float): The maximum number of tokens the bucket can hold.
        refill_rate (float): The rate at which tokens are added to the bucket per second.
        tokens (float): The current number of tokens available in the bucket.
        last_refill_timestamp (float): The timestamp of the last token refill.
    """
    
    def __init__(self, capacity: float, refill_rate: float) -> None:
        """
        Initializes the TokenBucket with a given capacity and refill rate.
        
        Args:
            capacity (float): The maximum number of tokens.
            refill_rate (float): The number of tokens added per second.
        """
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("Capacity and refill rate must be positive numbers.")
        
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_timestamp = time.time()
    
    def _refill_tokens(self) -> None:
        """
        Refills the bucket with tokens based on the elapsed time since the last refill.
        Ensures that the number of tokens does not exceed the capacity.
        """
        current_time = time.time()
        elapsed = current_time - self.last_refill_timestamp
        refill_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + refill_tokens)
        self.last_refill_timestamp = current_time
    
    def allow_request(self, tokens: Union[int, float] = 1) -> bool:
        """
        Attempts to consume a specified number of tokens from the bucket.
        
        Args:
            tokens (Union[int, float]): The number of tokens to consume. Defaults to 1.
        
        Returns:
            bool: True if the request is allowed (enough tokens available), False otherwise.
        """
        if tokens <= 0:
            raise ValueError("Number of tokens requested must be a positive number.")
        
        self._refill_tokens()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False