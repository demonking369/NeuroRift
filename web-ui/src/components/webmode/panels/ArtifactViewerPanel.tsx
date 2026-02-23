'use client';

import { useState, useEffect } from 'react';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { FileCode, FileText, File, Folder, ChevronRight, ChevronDown } from 'lucide-react';
import { FileNode } from '@/lib/webmode/adapter/interface';

// Simple recursive tree component
const FileTree = ({ node, onSelect }: { node: FileNode, onSelect: (path: string) => void }) => {
    const [open, setOpen] = useState(false);
    const isDir = node.type === 'directory';

    return (
        <div className="pl-2 select-none">
            <div
                className="flex items-center gap-1.5 py-1 text-xs text-neuro-text-secondary hover:text-cyan-300 cursor-pointer"
                onClick={() => isDir ? setOpen(!open) : onSelect(node.path)}
            >
                {isDir ? (
                    open ? <ChevronDown className="w-3 h-3 text-neuro-text-muted" /> : <ChevronRight className="w-3 h-3 text-neuro-text-muted" />
                ) : (
                    <span className="w-3" /> // spacer
                )}

                {isDir ? <Folder className="w-3 h-3 text-cyan-600" /> : <FileCode className="w-3 h-3 text-cyan-400" />}
                <span className="truncate">{node.name}</span>
            </div>
            {isDir && open && node.children && (
                <div className="border-l border-neuro-border/30 ml-1.5 pl-1">
                    {node.children.map(child => (
                        <FileTree key={child.path} node={child} onSelect={onSelect} />
                    ))}
                </div>
            )}
        </div>
    );
};

export function ArtifactViewerPanel() {
    const { adapter } = useWebModeContext();
    const [artifacts, setArtifacts] = useState<FileNode[]>([]);
    const [selectedContent, setSelectedContent] = useState<string | null>(null);
    const [selectedPath, setSelectedPath] = useState<string | null>(null);

    // Load initial mock artifacts for active session
    useEffect(() => {
        adapter.listArtifacts('current').then(setArtifacts);
    }, [adapter]);

    const handleSelect = async (path: string) => {
        setSelectedPath(path);
        try {
            const content = await adapter.readArtifact(path);
            setSelectedContent(content);
        } catch (e) {
            setSelectedContent(`Error loading artifact: ${e}`);
        }
    };

    return (
        <div className="h-full flex gap-3">
            <div className="w-1/3 flex flex-col min-w-[150px] border-r border-neuro-border/30 pr-2">
                <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs uppercase tracking-widest text-cyan-100 font-semibold">Artifacts</h3>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {artifacts.map(node => (
                        <FileTree key={node.path} node={node} onSelect={handleSelect} />
                    ))}
                </div>
            </div>

            <div className="flex-1 flex flex-col">
                <div className="text-[10px] text-neuro-text-muted mb-2 font-mono truncate px-2 py-1 bg-neuro-surface/50 rounded">
                    {selectedPath || 'Select an artifact...'}
                </div>
                <div className="flex-1 rounded-lg bg-black/40 border border-neuro-border/50 p-3 font-mono text-[10px] text-neuro-text-primary overflow-auto whitespace-pre custom-scrollbar">
                    {selectedContent}
                </div>
            </div>
        </div>
    );
}
