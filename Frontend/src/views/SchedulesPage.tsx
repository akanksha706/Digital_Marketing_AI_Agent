import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { ScheduledJob } from '../types';
import { Calendar, Clock, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { LinkedinIcon, InstagramIcon } from '../components/SocialIcons';

export const SchedulesPage: React.FC = () => {
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<ScheduledJob[]>('/schedules');
      setJobs(res.data);
    } catch {
      // Dev mock if table empty
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (jobId: number) => {
    try {
      await apiClient.post(`/schedules/${jobId}/retry`);
      fetchJobs();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to retry job dispatch.');
    }
  };

  const formatScheduledTime = (timeStr?: string, createdStr?: string) => {
    const raw = timeStr || createdStr;
    if (!raw) return 'Immediate';
    const parsed = new Date(raw);
    return isNaN(parsed.getTime()) ? 'Immediate' : parsed.toLocaleString();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between border-b border-slate-200 pb-6 mb-8">
        <div>
          <div className="flex items-center gap-2.5">
            <Calendar className="h-6 w-6 text-[#FFC20E]" />
            <h1 className="text-2xl font-black tracking-tight text-slate-900">Social Dispatch Queue</h1>
          </div>
          <p className="mt-1 text-xs text-slate-500 font-medium">
            Real-time status of scheduled and dispatched posts for LinkedIn and Instagram
          </p>
        </div>

        <button
          onClick={fetchJobs}
          className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-50 shadow-xs transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
          Refresh Queue
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400 font-medium">Loading scheduled queue...</div>
      ) : jobs.length === 0 ? (
        <div className="mx-auto max-w-md my-12 rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-xs">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 text-[#FFC20E] border border-amber-200/80 shadow-xs mb-4">
            <Clock className="h-7 w-7" />
          </div>
          <h3 className="text-base font-black text-slate-900">Queue is Clear</h3>
          <p className="mt-2 text-xs text-slate-500 leading-relaxed">
            No scheduled posts in queue. Approve posters in the Library or Studio and choose "Schedule" to queue them for LinkedIn or Instagram dispatch.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
          <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Job ID</th>
                <th className="px-6 py-3.5">Platform</th>
                <th className="px-6 py-3.5">Poster ID</th>
                <th className="px-6 py-3.5">Scheduled Time</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-4 font-mono font-medium text-slate-600">#{job.id}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold capitalize bg-slate-50 border border-slate-200 text-slate-800">
                      {job.platform === 'linkedin' ? (
                        <LinkedinIcon className="h-3.5 w-3.5 text-[#0077b5]" />
                      ) : (
                        <InstagramIcon className="h-3.5 w-3.5 text-pink-600" />
                      )}
                      {job.platform}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-700">Poster #{job.poster_id}</td>
                  <td className="px-6 py-4 text-slate-600">
                    <div className="flex items-center gap-1.5 text-slate-600 font-medium">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      {formatScheduledTime(job.scheduled_for || job.scheduled_time, job.created_at)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <span
                        className={`inline-flex items-center gap-1 w-fit rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase ${
                          job.status === 'success'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : job.status === 'failed'
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-amber-50 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {job.status === 'success' && <CheckCircle2 className="h-3 w-3" />}
                        {job.status === 'failed' && <AlertCircle className="h-3 w-3" />}
                        {job.status}
                      </span>
                      {job.status === 'failed' && (job.error_message || job.error_log) && (
                        <span className="text-[10px] text-rose-600 max-w-xs truncate" title={job.error_message || job.error_log || ''}>
                          {job.error_message || job.error_log}
                        </span>
                      )}
                      {job.status === 'success' && job.platform === 'linkedin' && (
                        <a
                          href="https://www.linkedin.com/in/anna-vance-09b599447/recent-activity/all/"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] text-blue-600 hover:underline flex items-center gap-1 font-medium"
                        >
                          View Live on LinkedIn ↗
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {job.status === 'failed' && (
                      <button
                        onClick={() => handleRetry(job.id)}
                        className="rounded-lg bg-slate-100 border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-800 hover:bg-slate-200 shadow-xs"
                      >
                        Retry Dispatch
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
