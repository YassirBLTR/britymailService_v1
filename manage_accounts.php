<?php
/**
 * Brityworks Account Manager
 * Web interface for managing email accounts credentials
 */

// Configuration
$accounts_file = __DIR__ . '/accounts.json';
$message = '';
$error = '';

// Helper function to read accounts
function readAccounts($file) {
    if (!file_exists($file)) {
        return [];
    }
    $content = file_get_contents($file);
    return json_decode($content, true) ?: [];
}

// Helper function to save accounts
function saveAccounts($file, $accounts) {
    $json = json_encode($accounts, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    return file_put_contents($file, $json) !== false;
}

// Handle form submissions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $accounts = readAccounts($accounts_file);
    
    // Add new account
    if (isset($_POST['action']) && $_POST['action'] === 'add') {
        $new_account = [
            'account_id' => trim($_POST['account_id']),
            'email' => trim($_POST['email']),
            'display_name' => trim($_POST['display_name']),
            'headers' => json_decode($_POST['headers'], true)
        ];
        
        // Validate
        if (empty($new_account['account_id']) || empty($new_account['email'])) {
            $error = 'Account ID and Email are required!';
        } elseif ($new_account['headers'] === null) {
            $error = 'Invalid JSON format for headers!';
        } else {
            // Check for duplicate account_id
            $exists = false;
            foreach ($accounts as $acc) {
                if ($acc['account_id'] === $new_account['account_id']) {
                    $exists = true;
                    break;
                }
            }
            
            if ($exists) {
                $error = 'Account ID already exists!';
            } else {
                $accounts[] = $new_account;
                if (saveAccounts($accounts_file, $accounts)) {
                    $message = 'Account added successfully!';
                } else {
                    $error = 'Failed to save accounts file!';
                }
            }
        }
    }
    
    // Edit existing account
    if (isset($_POST['action']) && $_POST['action'] === 'edit') {
        $account_id = $_POST['original_account_id'];
        $updated_account = [
            'account_id' => trim($_POST['account_id']),
            'email' => trim($_POST['email']),
            'display_name' => trim($_POST['display_name']),
            'headers' => json_decode($_POST['headers'], true)
        ];
        
        // Validate
        if (empty($updated_account['account_id']) || empty($updated_account['email'])) {
            $error = 'Account ID and Email are required!';
        } elseif ($updated_account['headers'] === null) {
            $error = 'Invalid JSON format for headers!';
        } else {
            $found = false;
            foreach ($accounts as $key => $acc) {
                if ($acc['account_id'] === $account_id) {
                    $accounts[$key] = $updated_account;
                    $found = true;
                    break;
                }
            }
            
            if ($found) {
                if (saveAccounts($accounts_file, $accounts)) {
                    $message = 'Account updated successfully!';
                } else {
                    $error = 'Failed to save accounts file!';
                }
            } else {
                $error = 'Account not found!';
            }
        }
    }
    
    // Delete account
    if (isset($_POST['action']) && $_POST['action'] === 'delete') {
        $account_id = $_POST['account_id'];
        $new_accounts = [];
        $found = false;
        
        foreach ($accounts as $acc) {
            if ($acc['account_id'] !== $account_id) {
                $new_accounts[] = $acc;
            } else {
                $found = true;
            }
        }
        
        if ($found) {
            if (saveAccounts($accounts_file, $new_accounts)) {
                $message = 'Account deleted successfully!';
            } else {
                $error = 'Failed to save accounts file!';
            }
        } else {
            $error = 'Account not found!';
        }
    }
}

// Read current accounts
$accounts = readAccounts($accounts_file);

// Get account for editing
$edit_account = null;
if (isset($_GET['edit'])) {
    foreach ($accounts as $acc) {
        if ($acc['account_id'] === $_GET['edit']) {
            $edit_account = $acc;
            break;
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brityworks Account Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            min-height: 150px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        
        .form-group small {
            display: block;
            margin-top: 5px;
            color: #666;
            font-size: 12px;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .btn-small {
            padding: 8px 16px;
            font-size: 14px;
            margin-right: 10px;
        }
        
        .accounts-list {
            margin-top: 20px;
        }
        
        .account-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        
        .account-item h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .account-item p {
            color: #666;
            margin-bottom: 5px;
        }
        
        .account-item .actions {
            margin-top: 15px;
        }
        
        .json-preview {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-height: 100px;
            overflow: auto;
            margin-top: 10px;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .empty-state svg {
            width: 100px;
            height: 100px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .form-buttons {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Brityworks Account Manager</h1>
            <p>Manage your email account credentials</p>
        </div>
        
        <?php if ($message): ?>
            <div class="alert alert-success">✅ <?php echo htmlspecialchars($message); ?></div>
        <?php endif; ?>
        
        <?php if ($error): ?>
            <div class="alert alert-error">❌ <?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        
        <!-- Add/Edit Account Form -->
        <div class="card">
            <h2><?php echo $edit_account ? '✏️ Edit Account' : '➕ Add New Account'; ?></h2>
            <form method="POST" action="">
                <input type="hidden" name="action" value="<?php echo $edit_account ? 'edit' : 'add'; ?>">
                <?php if ($edit_account): ?>
                    <input type="hidden" name="original_account_id" value="<?php echo htmlspecialchars($edit_account['account_id']); ?>">
                <?php endif; ?>
                
                <div class="form-group">
                    <label for="account_id">Account ID *</label>
                    <input type="text" id="account_id" name="account_id" 
                           value="<?php echo $edit_account ? htmlspecialchars($edit_account['account_id']) : ''; ?>" 
                           placeholder="e.g., account_1" required>
                    <small>Unique identifier for this account</small>
                </div>
                
                <div class="form-group">
                    <label for="email">Email Address *</label>
                    <input type="email" id="email" name="email" 
                           value="<?php echo $edit_account ? htmlspecialchars($edit_account['email']) : ''; ?>" 
                           placeholder="e.g., user@brityworks.com" required>
                </div>
                
                <div class="form-group">
                    <label for="display_name">Display Name</label>
                    <input type="text" id="display_name" name="display_name" 
                           value="<?php echo $edit_account ? htmlspecialchars($edit_account['display_name']) : ''; ?>" 
                           placeholder="e.g., Main Account">
                    <small>Friendly name to identify this account</small>
                </div>
                
                <div class="form-group">
                    <label for="headers">Headers (JSON) *</label>
                    <textarea id="headers" name="headers" required placeholder='{"accept": "application/json", "content-type": "application/json"}'><?php echo $edit_account ? json_encode($edit_account['headers'], JSON_PRETTY_PRINT) : ''; ?></textarea>
                    <small>Paste headers in JSON format</small>
                </div>
                
                <div class="form-buttons">
                    <button type="submit" class="btn btn-primary">
                        <?php echo $edit_account ? '💾 Update Account' : '➕ Add Account'; ?>
                    </button>
                    <?php if ($edit_account): ?>
                        <a href="manage_accounts.php" class="btn btn-secondary">❌ Cancel</a>
                    <?php endif; ?>
                </div>
            </form>
        </div>
        
        <!-- Accounts List -->
        <div class="card">
            <h2>📋 Existing Accounts (<?php echo count($accounts); ?>)</h2>
            
            <?php if (empty($accounts)): ?>
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                    <h3>No accounts yet</h3>
                    <p>Add your first account using the form above</p>
                </div>
            <?php else: ?>
                <div class="accounts-list">
                    <?php foreach ($accounts as $account): ?>
                        <div class="account-item">
                            <h3>🔑 <?php echo htmlspecialchars($account['display_name'] ?: $account['account_id']); ?></h3>
                            <p><strong>Account ID:</strong> <?php echo htmlspecialchars($account['account_id']); ?></p>
                            <p><strong>Email:</strong> <?php echo htmlspecialchars($account['email']); ?></p>
                            <p><strong>Headers:</strong> <?php echo count($account['headers']); ?> items</p>
                            
                            <div class="actions">
                                <a href="?edit=<?php echo urlencode($account['account_id']); ?>" class="btn btn-success btn-small">✏️ Edit</a>
                                <form method="POST" style="display: inline;" onsubmit="return confirm('Are you sure you want to delete this account?');">
                                    <input type="hidden" name="action" value="delete">
                                    <input type="hidden" name="account_id" value="<?php echo htmlspecialchars($account['account_id']); ?>">
                                    <button type="submit" class="btn btn-danger btn-small">🗑️ Delete</button>
                                </form>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
    
    <script>
        // Auto-format JSON on blur
        
        document.getElementById('headers').addEventListener('blur', function() {
            try {
                const parsed = JSON.parse(this.value);
                this.value = JSON.stringify(parsed, null, 2);
                this.style.borderColor = '#ddd';
            } catch (e) {
                this.style.borderColor = '#dc3545';
            }
        });
        
        // Scroll to form when editing
        <?php if ($edit_account): ?>
            window.scrollTo({ top: 0, behavior: 'smooth' });
        <?php endif; ?>
    </script>
</body>
</html>
