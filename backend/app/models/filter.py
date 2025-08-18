from datetime import datetime
from peewee import (
    AutoField, CharField, BooleanField, 
    DateTimeField, ForeignKeyField, IntegerField
)
from app.core.database import BaseModel
from app.models.base import Category
from app.models.article import User


class FilterRule(BaseModel):
    '''Filter rules for hiding articles based on criteria'''
    
    id = AutoField()
    user = ForeignKeyField(User, backref='filter_rules', on_delete='CASCADE')
    
    # Filter configuration
    name = CharField(max_length=100)  # User-friendly name for the filter
    filter_type = CharField(max_length=20, default='title_contains')  # title_contains, title_regex, author_contains, etc.
    filter_value = CharField(max_length=2000)  # The value to filter by
    
    # Scope
    category = ForeignKeyField(Category, backref='filter_rules', null=True, on_delete='CASCADE')  # null = apply to all
    feed_id = IntegerField(null=True)  # Optional: apply to specific feed
    
    # Settings
    is_active = BooleanField(default=True)
    case_sensitive = BooleanField(default=False)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'filter_rules'
        indexes = (
            # Index for efficient filtering
            (('user', 'is_active'), False),
            (('user', 'category'), False),
            (('created_at',), False),
        )
    
    def __str__(self):
        scope = f"Category: {self.category.name}" if self.category else "All categories"
        return f'{self.name} ({self.filter_type}: {self.filter_value}) - {scope}'
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def matches(self, article_title: str, article_author: str = None) -> bool:
        '''Check if an article matches this filter rule'''
        if not self.is_active:
            return False
            
        value = self.filter_value
        target_text = article_title if article_title else ''
        
        if self.filter_type == 'author_contains':
            target_text = article_author if article_author else ''
        
        if not self.case_sensitive:
            value = value.lower()
            target_text = target_text.lower()
        
        if self.filter_type == 'title_contains' or self.filter_type == 'author_contains':
            return self._evaluate_query(value, target_text)
        elif self.filter_type == 'title_exact':
            return value == target_text
        elif self.filter_type == 'title_not_contains':
            return not self._evaluate_query(value, target_text)
            
        return False
    
    def _evaluate_query(self, query: str, text: str) -> bool:
        '''Evaluate complex query with phrases and logical operators'''
        import re
        
        # Handle simple case - no quotes or operators
        if not any(op in query.upper() for op in [' OR ', ' AND ']) and '"' not in query:
            return query in text
        
        # Parse query into tokens
        tokens = self._parse_query(query)
        
        # Evaluate the parsed query
        return self._evaluate_tokens(tokens, text)
    
    def _parse_query(self, query: str) -> list:
        '''Parse query into tokens: phrases, words, and operators'''
        import re
        
        tokens = []
        current_pos = 0
        
        # Find quoted phrases first
        quote_pattern = r'"([^"]*)"'
        
        for match in re.finditer(quote_pattern, query):
            # Add any text before the quote as individual words
            before_quote = query[current_pos:match.start()].strip()
            if before_quote:
                words = before_quote.split()
                for word in words:
                    word = word.strip()
                    if word.upper() in ['AND', 'OR']:
                        tokens.append({'type': 'operator', 'value': word.upper()})
                    elif word:
                        tokens.append({'type': 'word', 'value': word})
            
            # Add the quoted phrase
            phrase = match.group(1)
            if phrase:
                tokens.append({'type': 'phrase', 'value': phrase})
            
            current_pos = match.end()
        
        # Add remaining text after last quote
        remaining = query[current_pos:].strip()
        if remaining:
            words = remaining.split()
            for word in words:
                word = word.strip()
                if word.upper() in ['AND', 'OR']:
                    tokens.append({'type': 'operator', 'value': word.upper()})
                elif word:
                    tokens.append({'type': 'word', 'value': word})
        
        return tokens
    
    def _evaluate_tokens(self, tokens: list, text: str) -> bool:
        '''Evaluate parsed tokens against text'''
        if not tokens:
            return False
        
        # Simple evaluation - no operator precedence for now
        results = []
        operators = []
        
        for token in tokens:
            if token['type'] == 'operator':
                operators.append(token['value'])
            else:
                # Evaluate phrase or word
                if token['type'] == 'phrase':
                    match = token['value'] in text
                else:  # word
                    match = token['value'] in text
                
                results.append(match)
        
        # If no operators, treat as AND (all must match)
        if not operators:
            return all(results)
        
        # Evaluate with operators (left to right)
        if not results:
            return False
        
        final_result = results[0]
        
        for i, operator in enumerate(operators):
            if i + 1 < len(results):
                if operator == 'AND':
                    final_result = final_result and results[i + 1]
                elif operator == 'OR':
                    final_result = final_result or results[i + 1]
        
        return final_result


# Update the model registry
FILTER_MODELS = [FilterRule]