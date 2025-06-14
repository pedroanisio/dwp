/**
 * Neural Chain Builder - Visual Plugin Chain Designer
 * Powered by Fabric.js and cyberpunk aesthetics
 */
class ChainBuilder {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.nodes = new Map();
        this.connections = new Map();
        this.selectedNode = null;
        this.selectedConnection = null;
        this.availablePlugins = [];
        this.chainData = {
            id: null,
            name: "Neural Processing Chain",
            description: "Describe your neural processing workflow...",
            nodes: [],
            connections: []
        };
        
        this.init();
    }
    
    async init() {
        console.log('🔗 Initializing Neural Chain Builder...');
        
        try {
            // Check if Fabric.js is loaded
            if (typeof fabric === 'undefined') {
                throw new Error('Fabric.js is not loaded. Please check the CDN link.');
            }
            
            await this.initializeCanvas();
            await this.loadAvailablePlugins();
            this.setupEventHandlers();
            this.showNotification('🚀 Chain Builder Ready! Drag plugins from the palette to the canvas', 'success');
            
            // Add helpful console message
            console.log('✅ Chain Builder initialized successfully!');
            console.log('💡 TIP: Drag plugins from the left palette to the canvas area');
            
        } catch (error) {
            console.error('❌ Failed to initialize chain builder:', error);
            this.showNotification(`Failed to initialize: ${error.message}`, 'error');
            
            // Show detailed error in console
            console.error('Error details:', error);
        }
    }
    
    async initializeCanvas() {
        const canvasElement = document.getElementById(this.canvasId);
        if (!canvasElement) {
            throw new Error(`Canvas element ${this.canvasId} not found`);
        }
        
        // Wait for DOM to be fully rendered
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Get proper dimensions
        const container = canvasElement.parentElement;
        
        let { width, height } = container.getBoundingClientRect();
        
        // If the container has no size, default to a visible size and warn the user.
        if (width === 0 || height === 0) {
            console.warn('⚠️ Canvas container has no dimensions. Falling back to 800x600. Please check parent element CSS.');
            width = 800;
            height = 600;
        }
        
        console.log(`📐 Initializing canvas: ${width}x${height}`);
        
        // Initialize Fabric.js canvas with proper dimensions
        this.canvas = new fabric.Canvas(this.canvasId, {
            width: width,
            height: height,
            backgroundColor: 'transparent',
            selection: true,
            preserveObjectStacking: true,
            allowTouchScrolling: false,
            enableRetinaScaling: true
        });
        
        // Canvas event handlers
        this.canvas.on('object:selected', (e) => this.onObjectSelected(e));
        this.canvas.on('selection:cleared', (e) => this.onSelectionCleared(e));
        this.canvas.on('object:moving', (e) => this.onObjectMoving(e));
        this.canvas.on('object:moved', (e) => this.onObjectMoved(e));
        
        // Handle window resize
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Ensure canvas is properly sized
        this.resizeCanvas();
        
        console.log('📐 Canvas initialized successfully');
    }
    
    async loadAvailablePlugins() {
        try {
            const response = await fetch('/api/plugins');
            const data = await response.json();
            
            if (data.success) {
                this.availablePlugins = data.plugins;
                this.renderPluginPalette();
                console.log(`🔌 Loaded ${this.availablePlugins.length} plugins`);
            } else {
                throw new Error('Failed to load plugins');
            }
        } catch (error) {
            console.error('Error loading plugins:', error);
            this.showNotification('Failed to load plugins', 'error');
        }
    }
    
    renderPluginPalette() {
        const palette = document.getElementById('plugin-palette');
        if (!palette) return;
        
        palette.innerHTML = '';
        
        this.availablePlugins.forEach(plugin => {
            const item = this.createPluginPaletteItem(plugin);
            palette.appendChild(item);
        });
    }
    
    createPluginPaletteItem(plugin) {
        const item = document.createElement('div');
        item.className = 'plugin-palette-item';
        item.dataset.pluginId = plugin.id;
        
        // Plugin icon based on type
        const icon = this.getPluginIcon(plugin);
        
        item.innerHTML = `
            <div class="plugin-icon">${icon}</div>
            <div class="plugin-name">${plugin.name}</div>
            <div class="plugin-description">${plugin.description}</div>
            <div class="drag-hint">Drag to canvas or click to add</div>
        `;
        
        // Enhanced drag and drop functionality
        item.draggable = true;
        
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('plugin-id', plugin.id);
            e.dataTransfer.setData('plugin-data', JSON.stringify(plugin));
            e.dataTransfer.effectAllowed = 'copy';
            
            // Add visual feedback
            item.classList.add('dragging');
            
            console.log(`🎯 Started dragging: ${plugin.name}`);
        });
        
        item.addEventListener('dragend', (e) => {
            // Remove visual feedback
            item.classList.remove('dragging');
        });
        
        // Click to add to center of canvas
        item.addEventListener('click', () => {
            // Calculate center position
            const canvasElement = document.getElementById(this.canvasId);
            if (canvasElement) {
                const rect = canvasElement.getBoundingClientRect();
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                this.addPluginNode(plugin.id, { x: centerX, y: centerY });
            } else {
                this.addPluginNode(plugin.id, { x: 400, y: 300 });
            }
        });
        
        // Hover effects
        item.addEventListener('mouseenter', () => {
            item.classList.add('hover');
        });
        
        item.addEventListener('mouseleave', () => {
            item.classList.remove('hover');
        });
        
        return item;
    }
    
    getPluginIcon(plugin) {
        const iconMap = {
            'text_stat': '📊',
            'doc_viewer': '📄',
            'pandoc_converter': '🔄',
            'json_to_xml': '🔀',
            'xml_to_json': '🔃',
            'web_sentence_analyzer': '🌐'
        };
        
        return iconMap[plugin.id] || '🔧';
    }
    
    setupEventHandlers() {
        // Toolbar buttons
        document.getElementById('save-chain')?.addEventListener('click', () => this.saveChain());
        document.getElementById('load-chain')?.addEventListener('click', () => this.showLoadChainDialog());
        document.getElementById('validate-chain')?.addEventListener('click', () => this.validateChain());
        document.getElementById('execute-chain')?.addEventListener('click', () => this.showExecutionDialog());
        document.getElementById('clear-canvas')?.addEventListener('click', () => this.clearCanvas());
        
        // Plugin search
        document.getElementById('plugin-search')?.addEventListener('input', (e) => {
            this.filterPlugins(e.target.value);
        });
        
        // Canvas drop zone - Enhanced with proper coordinate handling
        const canvasContainer = document.querySelector('.canvas-area');
        const canvasElement = document.getElementById(this.canvasId);
        
        if (canvasContainer && canvasElement) {
            // Enhanced drag over with visual feedback
            canvasContainer.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';
                
                // Add visual feedback
                canvasContainer.classList.add('dragover');
            });
            
            canvasContainer.addEventListener('dragleave', (e) => {
                // Remove visual feedback
                canvasContainer.classList.remove('dragover');
            });
            
            canvasContainer.addEventListener('drop', (e) => {
                e.preventDefault();
                
                // Remove visual feedback
                canvasContainer.classList.remove('dragover');
                
                const pluginId = e.dataTransfer.getData('plugin-id');
                if (pluginId) {
                    // Get accurate canvas coordinates using the reliable Fabric.js method
                    const pointer = this.canvas.getPointer(e);
                    const x = pointer.x;
                    const y = pointer.y;
                    
                    console.log(`🎯 Dropping plugin at: (${x}, ${y})`);
                    this.addPluginNode(pluginId, { x: x, y: y });
                }
            });
        }
        
        // Chain metadata updates
        document.getElementById('chain-name')?.addEventListener('input', (e) => {
            this.chainData.name = e.target.value;
        });
        
        document.getElementById('chain-description')?.addEventListener('input', (e) => {
            this.chainData.description = e.target.value;
        });
        
        // Execution modal
        document.getElementById('execute-confirm')?.addEventListener('click', () => this.executeChain());
        document.getElementById('execute-cancel')?.addEventListener('click', () => this.hideExecutionDialog());
        document.querySelector('.modal-close')?.addEventListener('click', () => this.hideExecutionDialog());
    }
    
    addPluginNode(pluginId, position) {
        const plugin = this.availablePlugins.find(p => p.id === pluginId);
        if (!plugin) {
            console.error(`Plugin ${pluginId} not found`);
            return;
        }
        
        const nodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Create visual node
        const nodeGroup = this.createVisualNode(nodeId, plugin, position);
        this.canvas.add(nodeGroup);
        this.canvas.renderAll();
        
        // Store node data
        const nodeData = {
            id: nodeId,
            type: 'plugin',
            plugin_id: pluginId,
            position: position,
            label: plugin.name,
            fabricObject: nodeGroup
        };
        
        this.nodes.set(nodeId, nodeData);
        this.chainData.nodes.push({
            id: nodeId,
            type: 'plugin',
            plugin_id: pluginId,
            position: position,
            label: plugin.name,
            config: {}
        });
        
        console.log(`➕ Added node: ${plugin.name} (${nodeId})`);
        this.showNotification(`Added ${plugin.name} node`, 'success');
        
        return nodeId;
    }
    
    // NOTE: The following function uses style properties to create the visual representation of the nodes.
    // This is part of the core functionality of the canvas and has been left as is.
    createVisualNode(nodeId, plugin, position) {
        const width = 180;
        const height = 120;
        
        // Node background
        const background = new fabric.Rect({
            width: width,
            height: height,
            fill: '#111111',
            stroke: '#00f5ff',
            strokeWidth: 2,
            rx: 0,
            ry: 0,
            originX: 'center',
            originY: 'center'
        });
        
        // Node header
        const header = new fabric.Text(plugin.name.toUpperCase(), {
            fontSize: 12,
            fill: '#00f5ff',
            fontFamily: 'Roboto Mono',
            fontWeight: 'bold',
            textAlign: 'center',
            originX: 'center',
            originY: 'center',
            top: -height / 2 + 15
        });
        
        // Plugin type
        const type = new fabric.Text('PLUGIN', {
            fontSize: 10,
            fill: '#b8bcc8',
            fontFamily: 'Roboto Mono',
            textAlign: 'center',
            originX: 'center',
            originY: 'center',
            top: -height / 2 + 35
        });
        
        // Plugin icon
        const icon = new fabric.Text(this.getPluginIcon(plugin), {
            fontSize: 24,
            textAlign: 'center',
            originX: 'center',
            originY: 'center',
            top: 0
        });
        
        // Status indicator
        const status = new fabric.Rect({
            width: width - 20,
            height: 20,
            fill: '#0a0a0a',
            stroke: '#3a86ff',
            strokeWidth: 1,
            originX: 'center',
            originY: 'center',
            top: height / 2 - 20,
            rx: 0,
            ry: 0
        });
        
        const statusText = new fabric.Text('READY', {
            fontSize: 8,
            fill: '#3a86ff',
            fontFamily: 'Roboto Mono',
            textAlign: 'center',
            originX: 'center',
            originY: 'center',
            top: height / 2 - 20
        });
        
        // Create group
        const group = new fabric.Group([background, header, type, icon, status, statusText], {
            left: position.x,
            top: position.y,
            selectable: true,
            hasControls: false,
            hasBorders: true,
            borderColor: '#ff006e',
            borderScaleFactor: 2,
            transparentCorners: false
        });
        
        // Store reference to node data
        group.nodeId = nodeId;
        group.pluginData = plugin;
        
        // Add event handlers
        group.on('selected', () => this.selectNode(nodeId));
        group.on('moving', () => this.updateNodePosition(nodeId, group));
        
        return group;
    }
    
    selectNode(nodeId) {
        this.selectedNode = nodeId;
        const nodeData = this.nodes.get(nodeId);
        
        if (nodeData) {
            this.showNodeProperties(nodeData);
            console.log(`🎯 Selected node: ${nodeData.label}`);
        }
    }
    
    showNodeProperties(nodeData) {
        const panel = document.getElementById('node-properties');
        if (!panel) return;
        
        const plugin = this.availablePlugins.find(p => p.id === nodeData.plugin_id);
        
        panel.innerHTML = `
            <div class="node-property">
                <label>Node ID</label>
                <input type="text" value="${nodeData.id}" readonly>
            </div>
            <div class="node-property">
                <label>Plugin</label>
                <input type="text" value="${plugin?.name || 'Unknown'}" readonly>
            </div>
            <div class="node-property">
                <label>Label</label>
                <input type="text" id="node-label" value="${nodeData.label}" placeholder="Custom label">
            </div>
            <div class="node-property">
                <label>Position</label>
                <div>
                    <input type="number" id="node-x" value="${Math.round(nodeData.position.x)}" placeholder="X">
                    <input type="number" id="node-y" value="${Math.round(nodeData.position.y)}" placeholder="Y">
                </div>
            </div>
            <div class="btn-group">
                <button class="btn btn-small btn-outline" onclick="window.chainBuilder.deleteNode('${nodeData.id}')">
                    🗑️ DELETE
                </button>
                <button class="btn btn-small btn-secondary" onclick="window.chainBuilder.showNodeConnections('${nodeData.id}')">
                    🔗 CONNECTIONS
                </button>
            </div>
            <div id="node-connections-panel"></div>
        `;
        
        // Add event handlers for property updates
        document.getElementById('node-label')?.addEventListener('input', (e) => {
            this.updateNodeLabel(nodeData.id, e.target.value);
        });
        
        document.getElementById('node-x')?.addEventListener('input', (e) => {
            this.updateNodePosition(nodeData.id, null, { x: parseInt(e.target.value) });
        });
        
        document.getElementById('node-y')?.addEventListener('input', (e) => {
            this.updateNodePosition(nodeData.id, null, { y: parseInt(e.target.value) });
        });
    }
    
    onSelectionCleared() {
        this.selectedNode = null;
        this.selectedConnection = null;
        this.showDefaultProperties();
    }
    
    showDefaultProperties() {
        const panel = document.getElementById('node-properties');
        if (!panel) return;
        
        panel.innerHTML = `
            <div class="text-center">
                <div>
                    <div>🔧</div>
                    <h4>No Node Selected</h4>
                    <p>
                        Click on a node to configure its properties and connections.
                    </p>
                </div>
            </div>
        `;
    }
    
    updateNodePosition(nodeId, fabricObject, newPosition) {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) return;
        
        if (newPosition) {
            nodeData.position = { ...nodeData.position, ...newPosition };
            if (fabricObject) {
                fabricObject.set({
                    left: nodeData.position.x,
                    top: nodeData.position.y
                });
                this.canvas.renderAll();
            }
        } else if (fabricObject) {
            nodeData.position = {
                x: fabricObject.left,
                y: fabricObject.top
            };
        }
        
        // Update chain data
        const chainNode = this.chainData.nodes.find(n => n.id === nodeId);
        if (chainNode) {
            chainNode.position = nodeData.position;
        }
    }
    
    updateNodeLabel(nodeId, newLabel) {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) return;
        
        nodeData.label = newLabel;
        
        // Update chain data
        const chainNode = this.chainData.nodes.find(n => n.id === nodeId);
        if (chainNode) {
            chainNode.label = newLabel;
        }
        
        console.log(`🏷️ Updated node label: ${newLabel}`);
    }
    
    deleteNode(nodeId) {
        if (!confirm('Delete this node? This action cannot be undone.')) {
            return;
        }
        
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) return;
        
        // Remove from canvas
        this.canvas.remove(nodeData.fabricObject);
        
        // Remove from data structures
        this.nodes.delete(nodeId);
        this.chainData.nodes = this.chainData.nodes.filter(n => n.id !== nodeId);
        this.chainData.connections = this.chainData.connections.filter(
            c => c.source_node_id !== nodeId && c.target_node_id !== nodeId
        );
        
        // Clear properties if this node was selected
        if (this.selectedNode === nodeId) {
            this.selectedNode = null;
            this.showDefaultProperties();
        }
        
        console.log(`❌ Deleted node: ${nodeData.label}`);
        this.showNotification(`Deleted ${nodeData.label}`, 'success');
    }
    
    filterPlugins(query) {
        const items = document.querySelectorAll('.plugin-palette-item');
        const searchTerm = query.toLowerCase();
        
        items.forEach(item => {
            const name = item.querySelector('.plugin-name').textContent.toLowerCase();
            const description = item.querySelector('.plugin-description').textContent.toLowerCase();
            
            if (name.includes(searchTerm) || description.includes(searchTerm)) {
                item.classList.remove('hidden');
            } else {
                item.classList.add('hidden');
            }
        });
    }
    
    async saveChain() {
        try {
            // Update chain metadata
            this.chainData.name = document.getElementById('chain-name')?.value || 'Untitled Chain';
            this.chainData.description = document.getElementById('chain-description')?.value || '';
            
            const response = await fetch('/api/chains', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    definition: this.chainData
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.chainData.id = result.chain_id;
                this.showNotification('Chain saved successfully!', 'success');
                console.log(`💾 Saved chain: ${this.chainData.name}`);
            } else {
                throw new Error('Failed to save chain');
            }
        } catch (error) {
            console.error('Error saving chain:', error);
            this.showNotification('Failed to save chain', 'error');
        }
    }
    
    async validateChain() {
        try {
            const response = await fetch('/api/chains/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.chainData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                const validation = result.validation;
                
                if (validation.is_valid) {
                    this.showNotification('✅ Chain validation passed!', 'success');
                } else {
                    let message = '❌ Chain validation failed:\n';
                    validation.errors.forEach(error => {
                        message += `• ${error}\n`;
                    });
                    
                    if (validation.warnings.length > 0) {
                        message += '\nWarnings:\n';
                        validation.warnings.forEach(warning => {
                            message += `⚠️ ${warning}\n`;
                        });
                    }
                    
                    alert(message);
                }
            }
        } catch (error) {
            console.error('Error validating chain:', error);
            this.showNotification('Failed to validate chain', 'error');
        }
    }
    
    showExecutionDialog() {
        const modal = document.getElementById('execution-modal');
        const inputData = document.getElementById('execution-input-data');
        
        if (modal && inputData) {
            // Set default input data
            inputData.value = JSON.stringify({
                "text": "Hello world! This is a test input for the neural chain."
            }, null, 2);
            
            modal.classList.add('active');
        }
    }
    
    hideExecutionDialog() {
        const modal = document.getElementById('execution-modal');
        const results = document.getElementById('execution-results');
        
        if (modal) {
            modal.classList.remove('active');
        }
        
        if (results) {
            results.classList.add('hidden');
        }
    }
    
    async executeChain() {
        if (!this.chainData.id) {
            alert('Please save the chain before executing it.');
            return;
        }
        
        try {
            const inputData = JSON.parse(document.getElementById('execution-input-data').value);
            
            this.showNotification('Executing chain...', 'info');
            
            const response = await fetch(`/api/chains/${this.chainData.id}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(inputData)
            });
            
            const result = await response.json();
            
            // Show results
            const resultsDiv = document.getElementById('execution-results');
            const outputDiv = document.getElementById('execution-output');
            
            if (resultsDiv && outputDiv) {
                outputDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                resultsDiv.classList.remove('hidden');
            }
            
            if (result.success) {
                this.showNotification('✅ Chain executed successfully!', 'success');
            } else {
                this.showNotification('❌ Chain execution failed', 'error');
            }
            
        } catch (error) {
            console.error('Error executing chain:', error);
            this.showNotification('Failed to execute chain', 'error');
        }
    }
    
    async clearCanvas() {
        if (!confirm('Clear all nodes and connections? This action cannot be undone.')) {
            return;
        }
    
        if (this.canvas) {
            this.canvas.clear();
            await this.canvas.dispose();
            await this.initializeCanvas();
        }
        
        this.nodes.clear();
        this.connections.clear();
        this.selectedNode = null;
        this.selectedConnection = null;
        
        this.chainData = {
            id: null,
            name: "Neural Processing Chain",
            description: "Describe your neural processing workflow...",
            nodes: [],
            connections: []
        };
        
        // Reset form fields
        document.getElementById('chain-name').value = this.chainData.name;
        document.getElementById('chain-description').value = this.chainData.description;
        
        this.showDefaultProperties();
        this.showNotification('Canvas cleared', 'success');
        
        console.log('🧹 Canvas cleared');
    }
    
    resizeCanvas() {
        const canvasElement = document.getElementById(this.canvasId);
        if (canvasElement && this.canvas) {
            const container = canvasElement.parentElement;
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            if (width > 0 && height > 0) {
                this.canvas.setDimensions({
                    width: width,
                    height: height
                });
                this.canvas.renderAll();
            } else {
                console.warn('⚠️ Skipping canvas resize because container dimensions are zero.');
            }
        }
    }
    
    showNotification(message, type = 'info') {
        if (window.Notifications) {
            window.Notifications.show(message, type);
        } else {
            // Fallback notification system
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    // Enhanced canvas event handlers
    onObjectSelected(e) {
        const obj = e.target;
        if (obj && obj.nodeId) {
            this.selectNode(obj.nodeId);
        }
    }
    
    onObjectMoving(e) {
        const obj = e.target;
        if (obj && obj.nodeId) {
            // Update position in real-time
            const nodeData = this.nodes.get(obj.nodeId);
            if (nodeData) {
                nodeData.position = {
                    x: obj.left,
                    y: obj.top
                };
            }
        }
    }
    
    onObjectMoved(e) {
        const obj = e.target;
        if (obj && obj.nodeId) {
            // Final position update
            this.updateNodePosition(obj.nodeId, obj);
            console.log(`📍 Node moved: ${obj.nodeId} to (${Math.round(obj.left)}, ${Math.round(obj.top)})`);
        }
    }
}

// Global chainBuilder instance will be created in the template 