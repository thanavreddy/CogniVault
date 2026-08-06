"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, File, Trash2, Search, Filter, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export default function DocumentsPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState([
    { id: '1', name: 'Employee_Handbook_2024.pdf', size: '2.4 MB', status: 'Ready', chunks: 145, date: '2024-02-15' },
    { id: '2', name: 'Q3_Financial_Report.pdf', size: '1.8 MB', status: 'Processing', chunks: 0, date: '2024-02-14' },
    { id: '3', name: 'Architecture_Diagrams.docx', size: '4.1 MB', status: 'Failed', chunks: 0, date: '2024-02-10' },
  ]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setIsUploading(true);
    // Mock upload
    setTimeout(() => {
      const newDocs = acceptedFiles.map((file, i) => ({
        id: `new-${i}`,
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
        status: 'Processing',
        chunks: 0,
        date: new Date().toISOString().split('T')[0]
      }));
      setDocuments(prev => [...newDocs, ...prev]);
      setIsUploading(false);
    }, 1500);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] } });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Documents</h2>
          <p className="text-muted-foreground">Manage your organization's knowledge base.</p>
        </div>
      </div>

      {/* Upload Zone */}
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-4">
          <Upload size={24} />
        </div>
        <h3 className="text-lg font-semibold mb-1">Click or drag files to upload</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Supports PDF, DOCX, TXT, MD up to 50MB
        </p>
        <Button variant="outline" disabled={isUploading}>
          {isUploading ? 'Uploading...' : 'Select Files'}
        </Button>
      </div>

      {/* Controls */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search documents..." className="pl-9" />
        </div>
        <Button variant="outline" className="flex items-center gap-2">
          <Filter size={16} /> Filter
        </Button>
      </div>

      {/* Document List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc) => (
          <Card key={doc.id} className="p-4 flex flex-col">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded text-blue-600 dark:text-blue-400">
                  <File size={20} />
                </div>
                <div>
                  <h4 className="font-medium text-sm truncate max-w-[150px]" title={doc.name}>
                    {doc.name}
                  </h4>
                  <p className="text-xs text-muted-foreground">{doc.size}</p>
                </div>
              </div>
              <div className="flex items-center">
                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive opacity-0 group-hover:opacity-100 transition-opacity">
                  <Trash2 size={14} />
                </Button>
              </div>
            </div>
            
            <div className="mt-auto flex items-center justify-between border-t pt-3">
              <div className="text-xs text-muted-foreground">
                {doc.chunks > 0 ? `${doc.chunks} chunks` : 'Processing chunks...'}
              </div>
              <div>
                {doc.status === 'Ready' && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                    Ready
                  </span>
                )}
                {doc.status === 'Processing' && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-500">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" /> Processing
                  </span>
                )}
                {doc.status === 'Failed' && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                    <AlertCircle size={12} /> Failed
                  </span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
