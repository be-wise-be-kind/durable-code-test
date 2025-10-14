# How to Refactor for Quality (Phase 2: Architectural Refactoring)

**Purpose**: Guide for fixing complexity and architectural issues requiring thoughtful design decisions

**Scope**: Component complexity, performance patterns, code organization, and architectural improvements

**Overview**: Phase 2 of the two-phase linting approach focuses on architectural violations that require design decisions. Only start Phase 2 after completing Phase 1 (basic linting). These fixes involve refactoring code structure, not just mechanical changes.

---

## When to Use This Guide

Use this guide when:
- ✅ Phase 1 (basic linting) is complete (`just lint-all` exits 0)
- ✅ Custom design linters show violations
- ✅ Code is functionally correct but architecturally complex
- ✅ React components have performance issues
- ✅ Code organization feels wrong

**Prerequisites**:
- All Phase 1 issues resolved
- All tests passing
- All security issues fixed

## Phase 2 Categories

### 1. Component Complexity

**React Components**:
Issues:
- Component too long (>300 lines)
- Too many props (>7)
- Too many useState calls (>5)
- Nested conditionals
- Mixed concerns (data + presentation)

**How to Refactor**:

**Pattern 1: Extract Custom Hooks**
```typescript
// Before: Complex component with mixed concerns
const UserDashboard = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const response = await api.getUsers();
        setUsers(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  return (
    <div>
      {loading && <Spinner />}
      {error && <Error message={error} />}
      {users.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
};

// After: Extract data fetching to custom hook
const useUsers = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const response = await api.getUsers();
        setUsers(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  return { users, loading, error };
};

const UserDashboard = () => {
  const { users, loading, error } = useUsers();

  if (loading) return <Spinner />;
  if (error) return <Error message={error} />;

  return (
    <div>
      {users.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
};
```

**Pattern 2: Split Into Smaller Components**
```typescript
// Before: Monolithic component
const ProductPage = ({ productId }) => {
  // 300+ lines of component code
  return (
    <div>
      {/* Product header */}
      {/* Product images */}
      {/* Product details */}
      {/* Reviews section */}
      {/* Related products */}
    </div>
  );
};

// After: Split into logical sub-components
const ProductPage = ({ productId }) => {
  return (
    <div>
      <ProductHeader productId={productId} />
      <ProductImages productId={productId} />
      <ProductDetails productId={productId} />
      <ReviewsSection productId={productId} />
      <RelatedProducts productId={productId} />
    </div>
  );
};
```

**Pattern 3: Reduce Props with Context**
```typescript
// Before: Prop drilling
const App = () => {
  const [theme, setTheme] = useState('light');
  return <Layout theme={theme} setTheme={setTheme} />;
};

const Layout = ({ theme, setTheme }) => {
  return <Sidebar theme={theme} setTheme={setTheme} />;
};

const Sidebar = ({ theme, setTheme }) => {
  return <ThemeToggle theme={theme} setTheme={setTheme} />;
};

// After: Use context
const ThemeContext = createContext<ThemeContextType | null>(null);

const App = () => {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <Layout />
    </ThemeContext.Provider>
  );
};

const Layout = () => <Sidebar />;
const Sidebar = () => <ThemeToggle />;

const ThemeToggle = () => {
  const { theme, setTheme } = useContext(ThemeContext)!;
  return <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} />;
};
```

### 2. Performance Optimization

**Common Performance Issues**:
- Unnecessary re-renders
- Missing memoization
- Expensive calculations in render
- Large lists without virtualization
- Polling loops instead of event-driven updates

**How to Optimize**:

**Pattern 1: Memoize Expensive Computations**
```typescript
// Before: Expensive calculation every render
const DataTable = ({ data }) => {
  const sortedData = data.sort((a, b) => a.value - b.value);
  return <Table data={sortedData} />;
};

// After: Memoize calculation
const DataTable = ({ data }) => {
  const sortedData = useMemo(
    () => data.sort((a, b) => a.value - b.value),
    [data]
  );
  return <Table data={sortedData} />;
};
```

**Pattern 2: Stabilize Callbacks with useCallback**
```typescript
// Before: New function every render
const UserList = ({ users }) => {
  const handleUserClick = (userId) => {
    console.log('Clicked:', userId);
  };

  return users.map(user => (
    <UserCard
      key={user.id}
      user={user}
      onClick={handleUserClick}  // New function every render
    />
  ));
};

// After: Stable function reference
const UserList = ({ users }) => {
  const handleUserClick = useCallback((userId: string) => {
    console.log('Clicked:', userId);
  }, []);

  return users.map(user => (
    <UserCard
      key={user.id}
      user={user}
      onClick={handleUserClick}  // Same function reference
    />
  ));
};
```

**Pattern 3: Event-Driven Instead of Polling**
```typescript
// Before: Polling loop
const useRealtimeData = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch('/api/data');
      setData(response.data);
    }, 1000);  // Poll every second

    return () => clearInterval(interval);
  }, []);

  return data;
};

// After: Event-driven with WebSocket
const useRealtimeData = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://api/stream');

    ws.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };

    return () => ws.close();
  }, []);

  return data;
};
```

See `.ai/docs/PERFORMANCE_OPTIMIZATION_STANDARDS.md` for complete patterns.

### 3. Code Organization

**Python Backend**:
Issues:
- Functions too long (>50 lines)
- Too many responsibilities in one class
- Circular dependencies
- God objects

**How to Refactor**:

**Pattern 1: Extract Helper Functions**
```python
# Before: Long function
def process_user_registration(data):
    # Validate email
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", data["email"]):
        raise ValueError("Invalid email")

    # Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(data["password"].encode(), salt)

    # Create user
    user = User(
        email=data["email"],
        password=hashed,
        created_at=datetime.now()
    )
    db.add(user)

    # Send welcome email
    send_email(
        to=user.email,
        subject="Welcome",
        body=f"Welcome {user.email}!"
    )

    return user

# After: Extract responsibilities
def validate_email(email: str) -> None:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        raise ValueError("Invalid email")

def hash_password(password: str) -> bytes:
    """Hash password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def create_user(email: str, hashed_password: bytes) -> User:
    """Create user in database."""
    user = User(
        email=email,
        password=hashed_password,
        created_at=datetime.now()
    )
    db.add(user)
    return user

def send_welcome_email(user: User) -> None:
    """Send welcome email to new user."""
    send_email(
        to=user.email,
        subject="Welcome",
        body=f"Welcome {user.email}!"
    )

def process_user_registration(data: dict) -> User:
    """Process user registration with validation and notifications."""
    validate_email(data["email"])
    hashed_password = hash_password(data["password"])
    user = create_user(data["email"], hashed_password)
    send_welcome_email(user)
    return user
```

**Pattern 2: Split Large Classes**
```python
# Before: God object
class UserManager:
    def create_user(self, data):
        ...

    def authenticate_user(self, email, password):
        ...

    def send_password_reset(self, email):
        ...

    def update_profile(self, user_id, data):
        ...

    def delete_account(self, user_id):
        ...

    def send_notification(self, user_id, message):
        ...

# After: Split by responsibility
class UserRepository:
    """Handle user data persistence."""
    def create(self, data): ...
    def update(self, user_id, data): ...
    def delete(self, user_id): ...

class AuthenticationService:
    """Handle user authentication."""
    def authenticate(self, email, password): ...
    def reset_password(self, email): ...

class NotificationService:
    """Handle user notifications."""
    def send_notification(self, user_id, message): ...
    def send_email(self, user_id, subject, body): ...
```

### 4. React Hook Dependencies

**Common Issues**:
- Missing dependencies in useEffect
- Stale closures
- Infinite loops from incorrect dependencies

**How to Fix**:

**Pattern 1: Complete Dependency Arrays**
```typescript
// Before: Missing dependencies
const MyComponent = ({ userId, fetchData }) => {
  useEffect(() => {
    fetchData(userId);
  }, []);  // ← Missing userId and fetchData

// After: Complete dependencies
const MyComponent = ({ userId, fetchData }) => {
  useEffect(() => {
    fetchData(userId);
  }, [userId, fetchData]);
```

**Pattern 2: Stabilize Function Dependencies**
```typescript
// Before: Function recreated every render causes infinite loop
const MyComponent = ({ userId }) => {
  const fetchData = async () => {
    const data = await api.getUser(userId);
    setUser(data);
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);  // ← fetchData changes every render

// After: Stabilize with useCallback
const MyComponent = ({ userId }) => {
  const fetchData = useCallback(async () => {
    const data = await api.getUser(userId);
    setUser(data);
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);
```

**Pattern 3: Functional Updates for Stale Closures**
```typescript
// Before: Stale closure
const Counter = () => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCount(count + 1);  // ← Always uses initial count value
    }, 1000);
    return () => clearInterval(interval);
  }, []);  // Empty deps causes stale closure

// After: Functional update
const Counter = () => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCount(prev => prev + 1);  // ← Uses current value
    }, 1000);
    return () => clearInterval(interval);
  }, []);  // Empty deps OK with functional update
```

## Decision Tree for Refactoring

When you encounter complexity issues, follow this decision tree:

```
Is the component >300 lines?
├─ YES → Split into smaller components
└─ NO → Continue

Does it have >5 useState calls?
├─ YES → Extract custom hook for state management
└─ NO → Continue

Does it mix data fetching and UI?
├─ YES → Extract data logic to custom hook
└─ NO → Continue

Does it pass >7 props?
├─ YES → Consider context or composition
└─ NO → Continue

Are there expensive calculations?
├─ YES → Add useMemo
└─ NO → Continue

Are callbacks causing re-renders?
├─ YES → Add useCallback
└─ NO → Component is likely well-structured
```

## Common Refactoring Mistakes to Avoid

### Mistake 1: Premature Optimization

❌ **Don't**:
```typescript
// Memoizing everything "just in case"
const Component = React.memo(({ value }) => {
  const memoized = useMemo(() => value * 2, [value]);
  const callback = useCallback(() => console.log(memoized), [memoized]);
  return <div onClick={callback}>{memoized}</div>;
});
```

✅ **Do**:
```typescript
// Only optimize when there's actual performance issue
const Component = ({ value }) => {
  return <div onClick={() => console.log(value * 2)}>{value * 2}</div>;
};
```

### Mistake 2: Over-Splitting Components

❌ **Don't**:
```typescript
// Creating tiny components for everything
const UserName = ({ name }) => <span>{name}</span>;
const UserEmail = ({ email }) => <span>{email}</span>;
const UserCard = ({ user }) => (
  <div>
    <UserName name={user.name} />
    <UserEmail email={user.email} />
  </div>
);
```

✅ **Do**:
```typescript
// Split only when it reduces complexity or enables reuse
const UserCard = ({ user }) => (
  <div>
    <span>{user.name}</span>
    <span>{user.email}</span>
  </div>
);
```

### Mistake 3: Complex Custom Hooks

❌ **Don't**:
```typescript
// Hooks that do too much
const useEverything = (userId) => {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  // 100+ lines of logic
  return { user, posts, comments, /* 20 other things */ };
};
```

✅ **Do**:
```typescript
// Focused, single-purpose hooks
const useUser = (userId) => { /* fetch user */ };
const usePosts = (userId) => { /* fetch posts */ };
const useComments = (postId) => { /* fetch comments */ };
```

## Validation Process

After refactoring:

### Step 1: Run Tests
```bash
just test
```
All tests must pass. If tests fail, your refactoring broke functionality.

### Step 2: Check Linting
```bash
just lint-all
```
Linting should still pass after refactoring.

### Step 3: Check Custom Linters
```bash
just lint-custom
```
Custom design linter violations should be resolved.

### Step 4: Manual Testing
- Test the feature in the browser
- Verify performance improvements (if applicable)
- Check that behavior is unchanged

### Step 5: Review Changes
```bash
git diff
```
Ensure refactoring is clean and logical.

## When to Ask for Help

Ask the user for guidance when:
- Multiple refactoring approaches are possible
- Performance tradeoffs need to be evaluated
- Breaking API changes might be needed
- Large-scale architectural changes are required

**Example**:
```
"I found that UserService has 15 methods and handles both authentication
and user management. I can refactor this in two ways:

Option 1: Split into AuthService and UserRepository
- Cleaner separation of concerns
- Requires updating 12 files that import UserService

Option 2: Keep together but extract helper functions
- Smaller change
- Still some coupling

Which approach would you prefer?"
```

## Success Criteria

Phase 2 is complete when:

✅ All of these are true:
- Code is well-organized and readable
- Components are appropriately sized
- Performance optimizations are in place where needed
- All tests pass
- `just lint-all` exits with code 0
- `just lint-custom` exits with code 0
- Manual testing confirms functionality

## Quick Reference

| Issue | Solution | Pattern |
|-------|----------|---------|
| Component >300 lines | Split into smaller components | Extract Component |
| >5 useState calls | Extract custom hook | Custom Hook |
| Mixed data + UI | Separate concerns | Custom Hook |
| >7 props | Use context or composition | Context/Composition |
| Expensive calc | Add useMemo | Memoization |
| Re-render issues | Add useCallback | Callback Stability |
| Missing deps | Complete dependency array | Hook Dependencies |
| Stale closures | Functional updates | Functional Update |
| Long function | Extract helpers | Extract Function |
| God object | Split by responsibility | Single Responsibility |

---

**Related Documentation**:
- `.ai/howto/how-to-fix-linting-errors.md` - Phase 1 (must complete first)
- `.ai/docs/PERFORMANCE_OPTIMIZATION_STANDARDS.md` - Performance patterns
- `.ai/docs/ERROR_HANDLING_STANDARDS.md` - Error handling refactoring
